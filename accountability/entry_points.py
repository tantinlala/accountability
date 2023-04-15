import argparse
from .secrets_parser import SecretsParser
from .bill_scraper import BillScraper
from .summarizer import Summarizer


def run_with_args(secrets_file):
    # Get secrets from a file
    secrets_parser = SecretsParser()
    secrets_parser.parse_secrets_file(secrets_file)

    # Required secrets will be provided to each class instance that uses it
    bill_scraper = BillScraper(secrets_parser)
    summarizer = Summarizer(secrets_parser)


def run():
    parser = argparse.ArgumentParser(
        prog='Run main entrypoint')
    parser.add_argument('secrets_file')  # positional argument
    args = parser.parse_args()
    run_with_args(args.secrets_file)


def setup():
    secrets_parser = SecretsParser()

    # Constructors should tell secrets_parser what secret it needs
    bill_scraper = BillScraper(secrets_parser)
    summarizer = Summarizer(secrets_parser)

    secrets_parser.create_template_secrets_file("template.yaml")
