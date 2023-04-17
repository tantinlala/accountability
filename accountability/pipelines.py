from accountability.secrets_parser import SecretsParser
from accountability.bill_scraper import BillScraper
from accountability.summarizer import Summarizer


def run_setup_pipeline(template_file):
    # First, create a secrets parser
    secrets_parser = SecretsParser()

    # Pass the secrets_parser into the constructors for these so that they can tell the parser what secrets they need
    bill_scraper = BillScraper(secrets_parser)
    summarizer = Summarizer(secrets_parser)

    # secrets_parser should now know how to create a template secrets file
    secrets_parser.create_template_secrets_file(template_file)


def run_bill_getting_pipeline(secrets_file, num_months):
    # Parse secrets from a file
    secrets_parser = SecretsParser()
    secrets_parser.parse_secrets_file(secrets_file)

    # Allow bill scraper to get required secrets
    bill_scraper = BillScraper(secrets_parser)

    # Get all the most recently voted upon senate bills
    bill_scraper.download_recent_senate_bills_and_votes(num_months)

    # Write all data to files
    bill_scraper.write_senate_bills_to_file()
    bill_scraper.write_metadata_to_file()


def run_estimate_summary_cost(text_file):
    # Estimate the cost to summarize a text file
    summarizer = Summarizer()
    summarizer.print_estimated_cost_of_file_summary(text_file)


def run_summarize_pipeline(secrets_file, text_file):
    # Parse secrets from a file
    secrets_parser = SecretsParser()
    secrets_parser.parse_secrets_file(secrets_file)

    # Allow summarizer to get required secrets
    summarizer = Summarizer(secrets_parser)

    # Summarize text file
    summarizer.summarize_file(text_file)
