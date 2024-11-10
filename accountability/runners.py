import datetime
import os
from accountability.secrets_parser import SecretsParser
from accountability.summarizer import Summarizer
from accountability.congress_api import CongressAPI
from accountability.hr_rollcall import HRRollCall
from accountability.congress_database import CongressDatabase
from accountability.reporter import Reporter
from accountability.file_utils import save_txt_if_not_exists, make_bill_path_string, make_dated_filename, get_previous_version_file, get_diff, make_summary_filepath, file_exists
from accountability.donorship import Donorship
from accountability.crp_categories import process_crp_categories
from accountability.industry_classifier import IndustryClassifier
from accountability.openai_assistant import OpenAIAssistant


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
    industries = process_crp_categories(crp_filepath)
    for catorder, industry in industries.items():
        congress_db.add_industry(catorder, industry)

    if year is None:
        year = datetime.datetime.now().year
    congress_db.update_last_hr_rollcall_for_year(year, rollcall_id)


def run_get_bill(secrets_file, congress, bill_id, datetime_string, save_directory):
    secrets_parser = SecretsParser()
    secrets_parser.parse_secrets_file(secrets_file)

    congress_api = CongressAPI(secrets_parser)
    datetime_obj = datetime.datetime.strptime(datetime_string, "%Y-%m-%dT%H:%M:%SZ")
    (bill_name, bill_datetime, bill_text) = congress_api.download_bill_text(congress, bill_id, datetime_obj)
    dated_bill_name = make_dated_filename(bill_datetime, bill_name)
    bill_save_directory = make_bill_path_string(save_directory, congress, bill_id)
    save_txt_if_not_exists(bill_save_directory, dated_bill_name, bill_text)


def run_get_amendment(secrets_file, congress, bill_id, datetime_string, save_directory):
    secrets_parser = SecretsParser()
    secrets_parser.parse_secrets_file(secrets_file)

    congress_api = CongressAPI(secrets_parser)
    datetime_obj = datetime.datetime.strptime(datetime_string, "%Y-%m-%dT%H:%M:%SZ")
    (amendment_name, amendment_datetime, amendment_text) = congress_api.download_amendment_text(congress, bill_id, datetime_obj)
    dated_amendment_name = make_dated_filename(amendment_datetime, amendment_name)
    bill_save_directory = make_bill_path_string(save_directory, congress, bill_id)
    save_txt_if_not_exists(bill_save_directory, dated_amendment_name, amendment_text)


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

    (bill_name, bill_datetime, bill_text, bill_title) = congress_api.download_bill_text(congress, bill_id, action_datetime)
    dated_bill_name = make_dated_filename(bill_datetime, bill_name)
    bill_filepath = save_txt_if_not_exists(save_directory, dated_bill_name, bill_text)

    dated_amendment_name = None
    amendment_filepath = None
    if hr_rollcall.is_amendment_vote():
        (amendment_name, amendment_datetime, amendment_text) = congress_api.download_amendment_text(congress, bill_id, action_datetime)
        dated_amendment_name = make_dated_filename(amendment_datetime, amendment_name)
        amendment_filepath = save_txt_if_not_exists(save_directory, dated_amendment_name, amendment_text)

    year = action_datetime.year

    # Add the roll call data to the database
    congress_db.add_rollcall_data(rollcall_id, year, action_datetime, question, bill_name, bill_datetime, dated_amendment_name, bill_title)

    # Save information on each legislator and each legislator's vote to the database
    for vote in hr_rollcall.get_votes():
        legislator_id = vote['id']
        congress_db.add_legislator(legislator_id, vote['name'], vote['state'], vote['party'])
        congress_db.add_vote(action_datetime, legislator_id, vote['vote'])

    return (bill_filepath, amendment_filepath)


def run_process_hr_rollcalls(secrets_file, save_directory):
    secrets_parser = SecretsParser()
    secrets_parser.parse_secrets_file(secrets_file)

    congress_api = CongressAPI(secrets_parser)
    congress_db = CongressDatabase()
    summarizer = Summarizer(secrets_parser)
    assistant = OpenAIAssistant(secrets_parser)
    classifier = IndustryClassifier(assistant=assistant, industries=congress_db.get_all_industries())
    reporter = Reporter(summarizer, classifier, congress_db)

    next_rollcall_id, year = congress_db.get_last_hr_rollcall_id()

    while True:
        next_rollcall_id += 1
        print(f"\nProcessing roll call {next_rollcall_id} for year {year}")

        hr_rollcall = HRRollCall()
        success = hr_rollcall.process_rollcall(year, next_rollcall_id)

        if not success:
            print(f"No roll call found for rollcall ID {next_rollcall_id} and year {year}. Trying next year.")
            year += 1
            next_rollcall_id = 1
            success = hr_rollcall.process_rollcall(year, next_rollcall_id)

        if not success:
            print(f"No roll call found for rollcall ID {next_rollcall_id} and year {year}. Exiting.")
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
                reporter.write_rollcall_report(old_rollcall_info['rollcall_id'], old_rollcall_info['year'], save_directory, bill_folder_string)

        (bill_filepath, amendment_filepath) = _save_rollcall_data(congress_api, congress_db, hr_rollcall, bill_folder_string)
        reporter.write_rollcall_report(next_rollcall_id, year, save_directory, bill_folder_string)

        congress_db.update_last_hr_rollcall_for_year(year, next_rollcall_id)


def run_classify_bills_industry(secrets_file, text_filepath):
    secrets_parser = SecretsParser()
    secrets_parser.parse_secrets_file(secrets_file)

    assistant = OpenAIAssistant(secrets_parser)
    congress_db = CongressDatabase()
    industries = congress_db.get_all_industries()

    with open(text_filepath, 'r') as file:
        text = file.read()

    classifier = IndustryClassifier(assistant=assistant, industries=industries)
    classification_results = classifier.classify(text)

    for industry_code in classification_results.industry_codes:
        description = industries[industry_code]
        print(f"Industry Code: {industry_code}, Description: {description}")


def run_create_hr_legislator_report(secrets_file, last_name, state_code, save_directory):
    secrets_parser = SecretsParser()
    secrets_parser.parse_secrets_file(secrets_file)
    
    congress_db = CongressDatabase()
    donorship = Donorship(secrets_parser)
    reporter = Reporter(None, None, congress_db)  # Assuming summarizer and classifier are not needed for this report

    # Get legislator ID
    legislator_id = congress_db.get_legislator_id(last_name, state_code)
    if not legislator_id:
        print(f"No legislator found with last name {last_name} in {state_code}")
        return

    # Check if top donors already exist in the database
    top_donors = congress_db.get_top_donors(legislator_id)
    if not top_donors:
        print(f"No top donors found for {last_name} in {state_code} in the database.")

        # Get top donors from online if not in the database
        top_donors = donorship.get_top_donors(last_name, state_code)
        if not top_donors:
            print(f"No top donors found for {last_name} in {state_code} from online.")
            return

        # Store top donors in the database
        for donor in top_donors['response']['industries']['industry']:
            industry_id = donor['@attributes']['industry_code']
            donation_amount = float(donor['@attributes']['total'])
            congress_db.add_legislator_industry(legislator_id, industry_id, donation_amount)

    # Generate report
    reporter.write_hr_legislator_report(legislator_id, save_directory)


if __name__ == '__main__':
    run_process_hr_rollcalls('secrets.yaml', 'results')
