from accountability.secrets_parser import SecretsParser
from accountability.bill_scraper import BillScraper
from accountability.summarizer import Summarizer


def run_summarize_pipeline(secrets_file, text_file):
    secrets_parser = SecretsParser()
    secrets_parser.parse_secrets_file(secrets_file)

    summarizer = Summarizer(secrets_parser)
    summarizer.summarize_file(text_file)


def run_calculate_tokens_pipeline(text_file):
    secrets_parser = SecretsParser()

    summarizer = Summarizer(secrets_parser)
    summarizer.calculate_tokens_for_file(text_file)


def run_bill_getting_pipeline(secrets_file, num_months):
    # Get secrets from a file
    secrets_parser = SecretsParser()
    secrets_parser.parse_secrets_file(secrets_file)

    # Required secrets will be provided to each class instance that uses it
    bill_scraper = BillScraper(secrets_parser)
    summarizer = Summarizer(secrets_parser)

    # Get all the most recently voted upon senate bills
    (bill_filenames, bill_metadata) = bill_scraper.get_recent_senate_bills(num_months, True)


def run_setup_pipeline(template_file):
    secrets_parser = SecretsParser()

    # Constructors will tell secrets_parser what secret it needs
    bill_scraper = BillScraper(secrets_parser)
    summarizer = Summarizer(secrets_parser)

    secrets_parser.create_template_secrets_file(template_file)

