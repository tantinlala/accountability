import argparse
from secrets_parser import SecretsParser
from bill_scraper import BillScraper
from summarizer import Summarizer


def run_with_args(secrets_file):
    # Get secrets from a file
    secrets_parser = SecretsParser()
    secrets_parser.parse_secrets_file(secrets_file)

    # Required secrets will be provided to each class instance that uses it
    bill_scraper = BillScraper(secrets_parser)
    bill_scraper.get_recent_senate_bills(2)
    summarizer = Summarizer(secrets_parser)


if __name__ == '__main__':
    run_with_args('secrets.yaml')


# This is an entry point
def run():
    parser = argparse.ArgumentParser(
        description='Run main entrypoint')
    parser.add_argument('secrets_file', help='yaml file containing secrets needed for this program')  # positional argument
    args = parser.parse_args()
    run_with_args(args.secrets_file)


# This is an entry point
def setup():
    parser = argparse.ArgumentParser(
        description='Create a template yaml file for storing secrets')

    secrets_parser = SecretsParser()

    # Constructors should tell secrets_parser what secret it needs
    bill_scraper = BillScraper(secrets_parser)
    summarizer = Summarizer(secrets_parser)

    secrets_parser.create_template_secrets_file("template.yaml")
