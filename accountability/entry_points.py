"""
This file contains functions that map to programs that can be called
from the command line upon installing the accountability pip package.
This should just map command line arguments to parameters passed into functions in pipelines.py
See entry_points in setup.py
"""

import os
import argparse
import json

from accountability.congress_api import CongressGovAPI
from accountability.secrets_parser import SecretsParser
from accountability.pipelines import run_bill_getting_pipeline, run_setup_pipeline, \
    run_summarize_pipeline, run_estimate_summary_cost

SECRETS_FILE_HELP_STRING = 'Yaml file containing secrets needed for this program'
TEXT_FILE_HELP_STRING = 'Text file containing content you want summarized'
SAVE_DIRECTORY_HELP_STRING = 'Directory to which you want to save file'


def setup():
    parser = argparse.ArgumentParser(
        description='Create a template yaml file for storing secrets (e.g. api keys)')
    parser.add_argument('-t', '--template', default='template.yaml')
    args = parser.parse_args()
    run_setup_pipeline(args.template)


def get_senate_bills():
    parser = argparse.ArgumentParser(
        description='Download text of senate bills voted upon within past m months and save them to a file. '
                    'Also saves vote positions of each senator to a file.')
    parser.add_argument('-s', '--secrets_file', help=SECRETS_FILE_HELP_STRING)
    parser.add_argument('-m', '--months', type=int, default=6)
    parser.add_argument('-d', '--save_directory', help=SAVE_DIRECTORY_HELP_STRING, default='')
    args = parser.parse_args()
    run_bill_getting_pipeline(args.secrets_file, args.months, args.save_directory)


def estimate_summary_cost():
    parser = argparse.ArgumentParser(
        description='Estimate the cost to summarize the contents of a text file')
    parser.add_argument('-t', '--text_file', help=TEXT_FILE_HELP_STRING)
    args = parser.parse_args()
    run_estimate_summary_cost(args.text_file)


def summarize():
    parser = argparse.ArgumentParser(
        description='Summarize a text document')
    parser.add_argument('-s', '--secrets_file', help=SECRETS_FILE_HELP_STRING)
    parser.add_argument('-t', '--text_file', help=TEXT_FILE_HELP_STRING)
    parser.add_argument('-d', '--save_directory', help=SAVE_DIRECTORY_HELP_STRING, default='')
    args = parser.parse_args()
    run_summarize_pipeline(args.secrets_file, args.text_file, args.save_directory)

def get_recent_bills():
    parser = argparse.ArgumentParser(
        description='Get recent bills')
    parser.add_argument('-s', '--secrets_file', default='secrets.yaml', help=SECRETS_FILE_HELP_STRING)
    args = parser.parse_args()

    # Assuming the API key is stored in an environment variable for security reasons
    # Get the API key from the secrets file
    secrets_parser = SecretsParser()
    secrets_parser.parse_secrets_file(args.secrets_file)
    api_key = secrets_parser.get_secret('congress', 'CONGRESS_API_KEY')

    if not api_key:
        print("API key is not set. Please set the CONGRESS_API_KEY environment variable or provide it in the secrets file.")
        return

    # Initialize the CongressGovAPI class with the API key
    congress_api = CongressGovAPI(api_key)

    # Get recent bills from the past month
    recent_bills = congress_api.get_recent_bills(months_back=1)

    # Check if there are any bills returned
    if recent_bills:
        print("Recent Bills:")
        for bill in recent_bills:
            print(json.dumps(bill, indent=4))
    else:
        print("No recent bills found.")
    if not api_key:
        print("API key is not set. Please set the CONGRESS_API_KEY environment variable.")
        return

    # Initialize the CongressGovAPI class with the API key
    congress_api = CongressGovAPI(api_key)

    # Get recent bills from the past month
    recent_bills = congress_api.get_recent_bills(months_back=1)

    # Check if there are any bills returned
    if recent_bills:
        print("Recent Bills:")
        for bill in recent_bills:
            print(json.dumps(bill, indent=4))
    else:
        print("No recent bills found.")