"""
This file contains functions that map to programs that can be called
from the command line upon installing the accountability pip package.
This should just map command line arguments to parameters passed into functions in pipelines.py
See entry_points in setup.py
"""

import argparse
from accountability.pipelines import run_bill_getting_pipeline, run_setup_pipeline, \
    run_summarize_pipeline, run_get_most_recently_voted_bills

SECRETS_FILE_HELP_STRING = 'Yaml file containing secrets needed for this program'
TEXT_FILE_HELP_STRING = 'Text file containing content you want summarized'
SAVE_DIRECTORY_HELP_STRING = 'Directory to which you want to save file'


def setup():
    parser = argparse.ArgumentParser(
        description='Create a template yaml file for storing secrets (e.g. api keys)')
    parser.add_argument('-t', '--template', default='template.yaml')
    parser.add_argument('-r', '--roll_call_id', type=int, default=0, help='The roll call ID to store in the database')
    args = parser.parse_args()
    run_setup_pipeline(args.template, args.roll_call_id)


def get_recently_introduced_bills():
    parser = argparse.ArgumentParser(
        description='Download text of senate bills voted upon within past m months and save them to a file. '
                    'Also saves vote positions of each senator to a file.')
    parser.add_argument('-s', '--secrets_file', help=SECRETS_FILE_HELP_STRING, default='secrets.yaml')
    parser.add_argument('-t', '--time_days', type=int, default=1)
    parser.add_argument('-d', '--save_directory', help=SAVE_DIRECTORY_HELP_STRING, default='bill_downloads')
    args = parser.parse_args()
    run_bill_getting_pipeline(args.secrets_file, args.time_days, args.save_directory)


def summarize():
    parser = argparse.ArgumentParser(
        description='Summarize a text document')
    parser.add_argument('-s', '--secrets_file', help=SECRETS_FILE_HELP_STRING, default='secrets.yaml')
    parser.add_argument('-t', '--text_file', help=TEXT_FILE_HELP_STRING)
    parser.add_argument('-d', '--save_directory', help=SAVE_DIRECTORY_HELP_STRING, default='bill_summaries')
    args = parser.parse_args()
    run_summarize_pipeline(args.secrets_file, args.text_file, args.save_directory)


def get_most_recently_voted_bills():
    parser = argparse.ArgumentParser(
        description='Download the text of the most recently voted upon HR bill')
    parser.add_argument('-s', '--secrets_file', help=SECRETS_FILE_HELP_STRING, default='secrets.yaml')
    parser.add_argument('-d', '--save_directory', help=SAVE_DIRECTORY_HELP_STRING, default='bill_downloads')
    args = parser.parse_args()
    run_get_most_recently_voted_bills(args.secrets_file, args.save_directory)