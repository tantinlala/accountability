from accountability.secrets_parser import SecretsParser
from accountability.summarizer import Summarizer
from accountability.congress_api import CongressAPI
from accountability.roll_call_processor import RollCallProcessor


def run_setup_pipeline(template_file):
    # First, create a secrets parser
    secrets_parser = SecretsParser()

    # Pass the secrets_parser into the constructors for these so that they can tell the parser what secrets they need
    CongressAPI(secrets_parser)
    Summarizer(secrets_parser)

    # secrets_parser should now know how to create a template secrets file
    secrets_parser.create_template_secrets_file(template_file)


def run_bill_getting_pipeline(secrets_file, num_days, save_directory):
    # Parse secrets from a file
    secrets_parser = SecretsParser()
    secrets_parser.parse_secrets_file(secrets_file)

    # Allow bill scraper to get required secrets
    bill_scraper = CongressAPI(secrets_parser)

    # Get all the most recently voted upon senate bills
    bill_scraper.get_list_of_recent_bills(num_days)

    # Write all data to files
    bill_scraper.save_bills_as_text(save_directory)

def run_get_most_recently_voted_bill(secrets_file, save_directory):
    # Parse secrets from a file
    secrets_parser = SecretsParser()
    secrets_parser.parse_secrets_file(secrets_file)

    bill_scraper = CongressAPI(secrets_parser)

    roll_call_processor = RollCallProcessor()
    roll_call_processor.process_roll_call(353)

    # Get the most recently voted upon senate bill
    bill_id = roll_call_processor.get_bill_id()
    action_datetime = roll_call_processor.get_action_datetime()
    bill_scraper.save_bill_as_text(bill_id, action_datetime, save_directory)


def run_estimate_summary_cost(text_file):
    # Estimate the cost to summarize a text file
    summarizer = Summarizer()
    summarizer.print_estimated_cost_of_file_summary(text_file)


def run_summarize_pipeline(secrets_file, text_file, save_directory):
    # Parse secrets from a file
    secrets_parser = SecretsParser()
    secrets_parser.parse_secrets_file(secrets_file)

    # Allow summarizer to get required secrets
    summarizer = Summarizer(secrets_parser)

    # Summarize text file
    summarizer.summarize_file(text_file, save_directory)
