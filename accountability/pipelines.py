from accountability.secrets_parser import SecretsParser
from accountability.bill_scraper import BillScraper
from accountability.summarizer import Summarizer


def run_main_pipeline(secrets_file, num_months):
    # Get secrets from a file
    secrets_parser = SecretsParser()
    secrets_parser.parse_secrets_file(secrets_file)

    # Required secrets will be provided to each class instance that uses it
    bill_scraper = BillScraper(secrets_parser)
    summarizer = Summarizer(secrets_parser)

    # First, get all the most recent senate bills
    (bill_filenames, bill_metadata) = bill_scraper.get_recent_senate_bills(num_months)

    # Next, tell summarizer to summarize each bill
    summarizer.summarize_files(bill_filenames)


def run_setup_pipeline(template_file):
    secrets_parser = SecretsParser()

    # Constructors will tell secrets_parser what secret it needs
    bill_scraper = BillScraper(secrets_parser)
    summarizer = Summarizer(secrets_parser)

    secrets_parser.create_template_secrets_file(template_file)

