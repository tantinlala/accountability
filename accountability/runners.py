import datetime
import os
from accountability.secrets_parser import SecretsParser
from accountability.summarizer import Summarizer
from accountability.openai_assistant import OpenAIAssistant
from accountability.congress_api import CongressAPI
from accountability.hr_rollcall import HRRollCall
from accountability.congress_database import CongressDatabase
from accountability.file_utils import save_if_not_exists, make_bill_path_string, make_filename, get_previous_version_file, get_diff, make_summary_filepath, file_exists


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
    bill_save_directory = make_bill_path_string(save_directory, congress, bill_id)
    save_if_not_exists(bill_save_directory, f"{bill_version_date}-{bill_name}", bill_text)


def run_get_amendment(secrets_file, congress, bill_id, datetime, save_directory):
    secrets_parser = SecretsParser()
    secrets_parser.parse_secrets_file(secrets_file)

    bill_scraper = CongressAPI(secrets_parser)
    (amendment_name, amendment_version_date, amendment_text) = bill_scraper.download_amendment_text(congress, bill_id, datetime)
    bill_save_directory = make_bill_path_string(save_directory, congress, bill_id)
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


def run_get_rollcalls_for_bill(secrets_file, congress, bill_id):
    secrets_parser = SecretsParser()
    secrets_parser.parse_secrets_file(secrets_file)

    bill_scraper = CongressAPI(secrets_parser)
    bill_scraper.get_rollcalls_for_bill(congress, bill_id)


def _save_rollcall_data(bill_scraper: CongressAPI, congress_db: CongressDatabase, hr_rollcall: HRRollCall, save_directory):
    rollcall_id = hr_rollcall.get_rollcall_id()
    congress = hr_rollcall.get_congress()
    bill_id = hr_rollcall.get_bill_id()
    action_datetime_string = hr_rollcall.get_datetime_string()
    question = hr_rollcall.get_vote_question()

    (bill_name, bill_version_date, bill_text) = bill_scraper.download_bill_text(congress, bill_id, action_datetime_string)
    bill_filepath = save_if_not_exists(save_directory, make_filename(bill_version_date, bill_name), bill_text)

    amendment_filepath = None
    if hr_rollcall.is_amendment_vote():
        (amendment_name, amendment_version_date, amendment_text) = bill_scraper.download_amendment_text(congress, bill_id, action_datetime_string)
        amendment_filepath = save_if_not_exists(save_directory, make_filename(amendment_version_date, amendment_name), amendment_text)

    year = int(action_datetime_string[:4])

    # Add the roll call data to the database
    congress_db.add_rollcall_data(rollcall_id, year, question, bill_name, amendment_name)

    # Save information on each congressman and each congressman's vote to the database
    for vote in hr_rollcall.get_votes():
        congressman_id = vote['id']
        congress_db.add_congressman(congressman_id, vote['name'], vote['state'], vote['party'])
        congress_db.add_vote(rollcall_id, year, congressman_id, vote['vote'])

    return (bill_filepath, amendment_filepath)

def _generate_rollcall_report(hr_rollcall: HRRollCall, openai_assistant: OpenAIAssistant, congress_db: CongressDatabase, bill_filepath, amendment_filepath, save_directory):
    summarizer = Summarizer(openai_assistant)
    bill_filename = os.path.basename(bill_filepath).split(".")[0]

    if previous_version_filepath := get_previous_version_file(bill_filepath):
        diff_text = get_diff(bill_filepath, previous_version_filepath)
        diff_filepath = save_if_not_exists(save_directory, bill_filename + "-diffs", diff_text)
        if file_exists(diff_summary_filepath := make_summary_filepath(diff_filepath)):
            print(f"Skipping summary because {diff_summary_filepath} already exists")
        elif diff_summary := summarizer.summarize_bill_diffs(diff_filepath):
            with open(diff_summary_filepath, 'w') as summary_file:
                summary_file.write(diff_summary)

    else: # No previous version
        if file_exists(bill_summary_filepath := make_summary_filepath(bill_filepath)):
            print(f"Skipping summary because {bill_summary_filepath} already exists")
        elif bill_summary := summarizer.summarize_bill(bill_filepath):
            with open(bill_summary_filepath, 'w') as summary_file:
                summary_file.write(bill_summary)

    hr_rollcall.save_rollcall_as_md(save_directory, bill_filepath, amendment_filepath)


def run_process_hr_rollcalls(secrets_file, save_directory):
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
        bill_folder_string = make_bill_path_string(save_directory, congress, bill_id)

        if not os.path.exists(bill_folder_string):
            os.makedirs(bill_folder_string)
            rollcall_urls = bill_scraper.get_older_rollcalls_for_bill(congress, bill_id, next_rollcall_id)
            for url in rollcall_urls:
                old_hr_rollcall = HRRollCall()
                old_hr_rollcall.process_rollcall_url(url)
                (bill_filepath, amendment_filepath) = _save_rollcall_data(bill_scraper, congress_db, old_hr_rollcall, bill_folder_string)

                _generate_rollcall_report(old_hr_rollcall, openai_assistant, congress_db, bill_filepath, amendment_filepath, bill_folder_string)

        (bill_filepath, amendment_filepath) = _save_rollcall_data(bill_scraper, congress_db, hr_rollcall, bill_folder_string)
        _generate_rollcall_report(hr_rollcall, openai_assistant, congress_db, bill_filepath, amendment_filepath, bill_folder_string)

        congress_db.update_last_hr_rollcall_for_year(year, next_rollcall_id)


if __name__ == '__main__':
    run_process_hr_rollcalls('secrets.yaml', 'results')
