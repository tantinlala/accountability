import datetime
import os
from accountability.secrets_parser import SecretsParser
from accountability.summarizer import Summarizer
from accountability.openai_assistant import OpenAIAssistant
from accountability.congress_api import CongressAPI
from accountability.hr_rollcall_processor import HRRollCallProcessor
from accountability.congress_database import CongressDatabase
from accountability.file_utils import save_if_not_exists, make_bill_directory, make_filename, get_previous_version_file, get_diff


def run_setup(template_file, roll_call_id):
    # First, create a secrets parser
    secrets_parser = SecretsParser()

    # Pass the secrets_parser into the constructors for these so that they can tell the parser what secrets they need
    CongressAPI(secrets_parser)
    OpenAIAssistant(secrets_parser)

    # secrets_parser should now know how to create a template secrets file
    secrets_parser.create_template_secrets_file(template_file)

    congress_db = CongressDatabase()

    year = datetime.datetime.now().year
    congress_db.update_hr_roll_call_id(year, roll_call_id)


def run_get_bill(secrets_file, congress, bill_id, datetime, save_directory):
    secrets_parser = SecretsParser()
    secrets_parser.parse_secrets_file(secrets_file)

    bill_scraper = CongressAPI(secrets_parser)
    (bill_name, bill_version_date, bill_text) = bill_scraper.download_bill_text(congress, bill_id, datetime)
    bill_save_directory = make_bill_directory(save_directory, congress, bill_id)
    save_if_not_exists(bill_save_directory, f"{bill_version_date}-{bill_name}", bill_text)


def run_get_amendment(secrets_file, congress, bill_id, datetime, save_directory):
    secrets_parser = SecretsParser()
    secrets_parser.parse_secrets_file(secrets_file)

    bill_scraper = CongressAPI(secrets_parser)
    (amendment_name, amendment_version_date, amendment_text) = bill_scraper.download_amendment_text(congress, bill_id, datetime)
    bill_save_directory = make_bill_directory(save_directory, congress, bill_id)
    save_if_not_exists(bill_save_directory, f"{amendment_version_date}-{amendment_name}", amendment_text)


def run_summarize_bill(secrets_file, text_file, save_directory):
    # Parse secrets from a file
    secrets_parser = SecretsParser()
    secrets_parser.parse_secrets_file(secrets_file)

    openai_assistant = OpenAIAssistant(secrets_parser)

    # Allow summarizer to get required secrets
    summarizer = Summarizer(openai_assistant)

    # Summarize text file
    summarizer.summarize_bill(save_directory, text_file)


def run_diff_with_previous(bill_file_path):
    # Get the part of the filename that is not part of the datetime
    # There should be 2 dashes in the datetime string
    bill_file_name = os.path.basename(bill_file_path)
    dash_splits = bill_file_name.split("-")
    bill_name = "-".join(dash_splits[3:])
    bill_save_directory = os.path.dirname(bill_file_path)
    bill_name_without_extension = os.path.splitext(bill_file_name)[0]

    previous_version_file_path = get_previous_version_file(bill_file_path, bill_name)

    if previous_version_file_path:
        diff_text = get_diff(bill_file_path, previous_version_file_path)
        save_if_not_exists(bill_save_directory, bill_name_without_extension + "-diffs", diff_text)


def run_summarize_diffs(secrets_file, diff_file_path):
    # Parse secrets from a file
    secrets_parser = SecretsParser()
    secrets_parser.parse_secrets_file(secrets_file)

    openai_assistant = OpenAIAssistant(secrets_parser)

    summarizer = Summarizer(openai_assistant)

    save_directory = os.path.dirname(diff_file_path)
    summarizer.summarize_bill_diffs(save_directory, diff_file_path)


def run_process_hr_rollcalls(secrets_file, save_directory):
    # Parse secrets from a file
    secrets_parser = SecretsParser()
    secrets_parser.parse_secrets_file(secrets_file)

    openai_assistant = OpenAIAssistant(secrets_parser)

    bill_scraper = CongressAPI(secrets_parser)
    congress_db = CongressDatabase()
    year = datetime.datetime.now().year

    next_roll_call_id = congress_db.get_most_recent_hr_roll_call_id(year)

    while True:
        next_roll_call_id += 1
        print(f"\nProcessing roll call {next_roll_call_id}")

        hr_rollcall_processor = HRRollCallProcessor()
        hr_rollcall_processor.process_rollcall(year, next_roll_call_id)
        congress = hr_rollcall_processor.get_congress()
        bill_id = hr_rollcall_processor.get_bill_id()
        if bill_id is None:
            print(f"No roll call found for {next_roll_call_id}")
            break

        action_datetime = hr_rollcall_processor.get_action_datetime()

        bill_save_directory = make_bill_directory(save_directory, congress, bill_id)
        if not os.path.exists(bill_save_directory):
            os.makedirs(bill_save_directory)

        (bill_name, bill_version_date, bill_text) = bill_scraper.download_bill_text(congress, bill_id, action_datetime)
        bill_file_path = save_if_not_exists(bill_save_directory, make_filename(bill_version_date, bill_name), bill_text)

        previous_version_file_path = get_previous_version_file(bill_file_path, bill_name + ".txt")

        summarizer = Summarizer(openai_assistant)
        if previous_version_file_path:
            diff_text = get_diff(bill_file_path, previous_version_file_path)
            diff_file_path = save_if_not_exists(bill_save_directory, make_filename(bill_version_date, bill_name) + "-diffs", diff_text)
            summarizer.summarize_bill_diffs(bill_save_directory, diff_file_path)
        else:
            summarizer.summarize_bill(bill_save_directory, bill_file_path)

        # If the vote was on an amendment, download the amendment text
        amendment_file_path = None
        if hr_rollcall_processor.is_amendment_vote():
            (amendment_name, amendment_version_date, amendment_text) = bill_scraper.download_amendment_text(congress, bill_id, action_datetime)
            save_if_not_exists(bill_save_directory, make_filename(amendment_version_date, amendment_name), amendment_text)

        hr_rollcall_processor.save_rollcall_as_md(bill_save_directory, bill_file_path, amendment_file_path)
        congress_db.update_hr_roll_call_id(year, next_roll_call_id)


if __name__ == '__main__':
    run_process_hr_rollcalls('secrets.yaml', 'results')
