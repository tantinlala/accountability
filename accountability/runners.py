import datetime
import os
from accountability.secrets_parser import SecretsParser
from accountability.summarizer import Summarizer
from accountability.openai_assistant import OpenAIAssistant
from accountability.congress_api import CongressAPI
from accountability.hr_rollcall import HRRollCall
from accountability.congress_database import CongressDatabase
from accountability.file_utils import save_if_not_exists, make_bill_directory, make_filename, get_previous_version_file, get_diff, make_summary_filepath, file_exists


def run_setup(template_file, rollcall_id):
    # First, create a secrets parser
    secrets_parser = SecretsParser()

    # Pass the secrets_parser into the constructors for these so that they can tell the parser what secrets they need
    CongressAPI(secrets_parser)
    OpenAIAssistant(secrets_parser)

    # secrets_parser should now know how to create a template secrets file
    secrets_parser.create_template_secrets_file(template_file)

    congress_db = CongressDatabase()

    year = datetime.datetime.now().year
    congress_db.update_last_hr_rollcall_for_year(year, rollcall_id)


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


def run_summarize(secrets_file, filepath):
    secrets_parser = SecretsParser()
    secrets_parser.parse_secrets_file(secrets_file)

    openai_assistant = OpenAIAssistant(secrets_parser)
    summarizer = Summarizer(openai_assistant)

    if "diffs" in filepath:
        summarize_function = summarizer.summarize_bill_diffs
    else:
        summarize_function = summarizer.summarize_bill

    if file_exists(summary_filepath := make_summary_filepath(filepath)):
        print(f"Skipping summary because {summary_filepath} already exists")
    elif summary := summarize_function(filepath):
        with open(summary_filepath, 'w') as summary_file:
            summary_file.write(summary)


def run_diff_with_previous(bill_filepath):
    previous_version_filepath = get_previous_version_file(bill_filepath)

    bill_file_name = os.path.basename(bill_filepath)
    bill_save_directory = os.path.dirname(bill_filepath)
    bill_name_without_extension = os.path.splitext(bill_file_name)[0]

    if previous_version_filepath:
        diff_text = get_diff(bill_filepath, previous_version_filepath)
        save_if_not_exists(bill_save_directory, bill_name_without_extension + "-diffs", diff_text)


def run_summarize_diffs(secrets_file, filepath):
    secrets_parser = SecretsParser()
    secrets_parser.parse_secrets_file(secrets_file)

    openai_assistant = OpenAIAssistant(secrets_parser)
    summarizer = Summarizer(openai_assistant)

    if file_exists(summary_filepath := make_summary_filepath(filepath)):
        print(f"Skipping summary because {summary_filepath} already exists")
    elif summary := summarizer.summarize_bill_diffs(filepath):
        with open(summary_filepath, 'w') as summary_file:
            summary_file.write(summary)


def run_process_hr_rollcalls(secrets_file, save_directory):
    # Parse secrets from a file
    secrets_parser = SecretsParser()
    secrets_parser.parse_secrets_file(secrets_file)

    openai_assistant = OpenAIAssistant(secrets_parser)

    bill_scraper = CongressAPI(secrets_parser)
    congress_db = CongressDatabase()
    year = datetime.datetime.now().year

    if not congress_db.year_exists(year):
        congress_db.add_year(year)

    next_rollcall_id = congress_db.get_last_hr_rollcall_for_year(year)

    while True:
        next_rollcall_id += 1
        print(f"\nProcessing roll call {next_rollcall_id} for year {year}")

        hr_rollcall = HRRollCall()
        success = hr_rollcall.process_rollcall(year, next_rollcall_id)
        if not success:
            print(f"No roll call found for {next_rollcall_id}")
            break

        congress = hr_rollcall.get_congress()
        bill_id = hr_rollcall.get_bill_id()
        action_datetime = hr_rollcall.get_action_datetime()

        bill_save_directory = make_bill_directory(save_directory, congress, bill_id)
        if not os.path.exists(bill_save_directory):
            os.makedirs(bill_save_directory)

        (bill_name, bill_version_date, bill_text) = bill_scraper.download_bill_text(congress, bill_id, action_datetime)
        bill_filepath = save_if_not_exists(bill_save_directory, make_filename(bill_version_date, bill_name), bill_text)

        summarizer = Summarizer(openai_assistant)
        amendment_name = None
        amendment_filepath = None

        if hr_rollcall.is_amendment_vote():
            (amendment_name, amendment_version_date, amendment_text) = bill_scraper.download_amendment_text(congress, bill_id, action_datetime)
            amendment_filepath = save_if_not_exists(bill_save_directory, make_filename(amendment_version_date, amendment_name), amendment_text)
            # TODO: check whether there was a previous vote on this amendment and find all of the changes in votes?
            # TODO: add data related to amendment to report

        if previous_version_filepath := get_previous_version_file(bill_filepath):
            diff_text = get_diff(bill_filepath, previous_version_filepath)
            diff_filepath = save_if_not_exists(bill_save_directory, make_filename(bill_version_date, bill_name) + "-diffs", diff_text)
            if file_exists(diff_summary_filepath := make_summary_filepath(diff_filepath)):
                print(f"Skipping summary because {diff_summary_filepath} already exists")
            elif diff_summary := summarizer.summarize_bill_diffs(diff_filepath):
                with open(diff_summary_filepath, 'w') as summary_file:
                    summary_file.write(diff_summary)
            # TODO: check whether there was a previous vote for the same question and find all of the changes in votes?
            # TODO: create report specific to diffs in versions and votes

        else: # No previous version
            if file_exists(bill_summary_filepath := make_summary_filepath(bill_filepath)):
                print(f"Skipping summary because {bill_summary_filepath} already exists")
            elif bill_summary := summarizer.summarize_bill(bill_filepath):
                with open(bill_summary_filepath, 'w') as summary_file:
                    summary_file.write(bill_summary)

        # Add the roll call data to the database
        congress_db.add_rollcall_data(next_rollcall_id, year, hr_rollcall.get_vote_question(), bill_name, amendment_name)

        # Save information on each congressman and each congressman's vote to the database
        for vote in hr_rollcall.get_votes():
            congressman_id = vote['id']
            if not congress_db.congressman_exists(congressman_id):
                congress_db.add_congressman(congressman_id, vote['name'], vote['state'], vote['party'])
            congress_db.add_vote(next_rollcall_id, congressman_id, vote['vote'])

        hr_rollcall.save_rollcall_as_md(bill_save_directory, bill_filepath, amendment_filepath)
        congress_db.update_last_hr_rollcall_for_year(year, next_rollcall_id)


if __name__ == '__main__':
    run_process_hr_rollcalls('secrets.yaml', 'results')
