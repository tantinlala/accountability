import datetime
import os
from accountability.secrets_parser import SecretsParser
from accountability.summarizer import Summarizer
from accountability.congress_api import CongressAPI
from accountability.hr_rollcall import HRRollCall
from accountability.congress_database import CongressDatabase
from accountability.reporter import Reporter
from accountability.file_utils import save_txt_if_not_exists, make_bill_path_string, make_filename, get_previous_version_file, get_diff, make_summary_filepath, file_exists
from accountability.donorship import Donorship
from accountability.crp_categories import process_crp_categories


def run_setup(template_file, rollcall_id, year, crp_filepath):
    # First, create a secrets parser
    secrets_parser = SecretsParser()

    # Pass the secrets_parser into the constructors for these so that they can tell the parser what secrets they need
    CongressAPI(secrets_parser)
    Summarizer(secrets_parser)
    Donorship(secrets_parser)

    # secrets_parser should now know how to create a template secrets file
    secrets_parser.create_template_secrets_file(template_file)

    # Initialize the database
    congress_db = CongressDatabase()

    # Store CRP categories in the database
    crp_categories = process_crp_categories(crp_filepath)
    for catorder, industry in crp_categories.items():
        congress_db.add_crp_category(catorder, industry)

    if year is None:
        year = datetime.datetime.now().year
    congress_db.update_last_hr_rollcall_for_year(year, rollcall_id)


def run_get_bill(secrets_file, congress, bill_id, datetime_string, save_directory):
    secrets_parser = SecretsParser()
    secrets_parser.parse_secrets_file(secrets_file)

    congress_api = CongressAPI(secrets_parser)
    datetime_obj = datetime.datetime.strptime(datetime_string, "%Y-%m-%dT%H:%M:%SZ")
    (bill_name, bill_version_date, bill_text) = congress_api.download_bill_text(congress, bill_id, datetime_obj)
    bill_save_directory = make_bill_path_string(save_directory, congress, bill_id)
    save_txt_if_not_exists(bill_save_directory, f"{bill_version_date}-{bill_name}", bill_text)


def run_get_amendment(secrets_file, congress, bill_id, datetime_string, save_directory):
    secrets_parser = SecretsParser()
    secrets_parser.parse_secrets_file(secrets_file)

    congress_api = CongressAPI(secrets_parser)
    datetime_obj = datetime.datetime.strptime(datetime_string, "%Y-%m-%dT%H:%M:%SZ")
    (amendment_name, amendment_version_date, amendment_text) = congress_api.download_amendment_text(congress, bill_id, datetime_obj)
    bill_save_directory = make_bill_path_string(save_directory, congress, bill_id)
    save_txt_if_not_exists(bill_save_directory, f"{amendment_version_date}-{amendment_name}", amendment_text)


def run_summarize(secrets_file, filepath):
    secrets_parser = SecretsParser()
    secrets_parser.parse_secrets_file(secrets_file)

    summarizer = Summarizer(secrets_parser)

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
        save_txt_if_not_exists(bill_save_directory, bill_name_without_extension + "-diffs", diff_text)


def run_get_older_rollcalls_for_bill(secrets_file, congress, bill_id, rollcall_id, year, save_directory):
    secrets_parser = SecretsParser()
    secrets_parser.parse_secrets_file(secrets_file)
    congress_db = CongressDatabase()
    congress_api = CongressAPI(secrets_parser)

    bill_folder_string = make_bill_path_string(save_directory, congress, bill_id)

    if not os.path.exists(bill_folder_string):
        os.makedirs(bill_folder_string)

    rollcall_urls = congress_api.get_older_rollcalls_for_bill(congress, bill_id, rollcall_id, year)
    for url in rollcall_urls:
        old_hr_rollcall = HRRollCall()
        old_hr_rollcall.process_rollcall_url(url)
        _save_rollcall_data(congress_api, congress_db, old_hr_rollcall, bill_folder_string)


def _save_rollcall_data(congress_api: CongressAPI, congress_db: CongressDatabase, hr_rollcall: HRRollCall, save_directory):
    rollcall_id = hr_rollcall.get_rollcall_id()
    congress = hr_rollcall.get_congress()
    bill_id = hr_rollcall.get_bill_id()
    action_datetime = hr_rollcall.get_datetime()
    question = hr_rollcall.get_vote_question()

    (bill_name, bill_version_date, bill_text) = congress_api.download_bill_text(congress, bill_id, action_datetime)
    dated_bill_name = make_filename(bill_version_date, bill_name)
    bill_filepath = save_txt_if_not_exists(save_directory, dated_bill_name, bill_text)

    dated_amendment_name = None
    amendment_filepath = None
    if hr_rollcall.is_amendment_vote():
        (amendment_name, amendment_version_date, amendment_text) = congress_api.download_amendment_text(congress, bill_id, action_datetime)
        dated_amendment_name = make_filename(amendment_version_date, amendment_name)
        amendment_filepath = save_txt_if_not_exists(save_directory, dated_amendment_name, amendment_text)

    year = action_datetime.year

    # Add the roll call data to the database
    congress_db.add_rollcall_data(rollcall_id, year, action_datetime, question, dated_bill_name, dated_amendment_name)

    # Save information on each congressman and each congressman's vote to the database
    for vote in hr_rollcall.get_votes():
        congressman_id = vote['id']
        congress_db.add_congressman(congressman_id, vote['name'], vote['state'], vote['party'])
        congress_db.add_vote(action_datetime, congressman_id, vote['vote'])

    return (bill_filepath, amendment_filepath)


def _generate_rollcall_report(rollcall_id, year, summarizer: Summarizer, congress_db: CongressDatabase, save_directory, bill_folder_string):
    reporter = Reporter(summarizer)
    reporter.write_rollcall_report(rollcall_id, year, congress_db, save_directory, bill_folder_string)


def run_process_hr_rollcalls(secrets_file, save_directory):
    secrets_parser = SecretsParser()
    secrets_parser.parse_secrets_file(secrets_file)

    congress_api = CongressAPI(secrets_parser)
    congress_db = CongressDatabase()
    summarizer = Summarizer(secrets_parser)

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
            rollcall_urls = congress_api.get_older_rollcalls_for_bill(congress, bill_id, next_rollcall_id, year)
            old_rollcall_info_list = []
            for url in rollcall_urls:
                old_hr_rollcall = HRRollCall()
                old_hr_rollcall.process_rollcall_url(url)
                old_rollcall_info = dict()
                old_rollcall_info['rollcall_id'] = old_hr_rollcall.get_rollcall_id()
                old_rollcall_info['year'] = old_hr_rollcall.get_datetime().year
                (bill_filepath, amendment_filepath) = _save_rollcall_data(congress_api, congress_db, old_hr_rollcall, bill_folder_string)
                old_rollcall_info['bill'] = bill_filepath
                old_rollcall_info['amendment'] = amendment_filepath
                old_rollcall_info_list.append(old_rollcall_info)

            for old_rollcall_info in old_rollcall_info_list:
                _generate_rollcall_report(old_rollcall_info['rollcall_id'], old_rollcall_info['year'], summarizer, congress_db, save_directory, bill_folder_string)

        (bill_filepath, amendment_filepath) = _save_rollcall_data(congress_api, congress_db, hr_rollcall, bill_folder_string)
        _generate_rollcall_report(next_rollcall_id, year, summarizer, congress_db, save_directory, bill_folder_string)

        congress_db.update_last_hr_rollcall_for_year(year, next_rollcall_id)


def run_get_donors_for_legislator(secrets_file, last_name, state_code):
    secrets_parser = SecretsParser()
    secrets_parser.parse_secrets_file(secrets_file)

    donorship = Donorship(secrets_parser)
    donorship.get_top_donors(last_name, state_code)


def run_create_hr_legislator_profile(secrets_file, last_name, state_code):
    secrets_parser = SecretsParser()
    secrets_parser.parse_secrets_file(secrets_file)

    donorship = Donorship(secrets_parser)


    # First, check whether the legislator is already in the database

    donorship.get_top_donors(last_name, state_code)

if __name__ == '__main__':
    run_process_hr_rollcalls('secrets.yaml', 'results')
