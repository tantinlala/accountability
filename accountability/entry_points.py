"""
This file contains functions that map to programs that can be called
from the command line upon installing the accountability pip package.
This should just map command line arguments to parameters passed into functions in pipelines.py
See entry_points in setup.py
"""

import argparse
from accountability.pipelines import run_bill_getting_pipeline, run_setup_pipeline, \
    run_summarize_pipeline, run_estimate_summary_cost

SECRETS_FILE_HELP_STRING = 'Yaml file containing secrets needed for this program'
TEXT_FILE_HELP_STRING = 'Text file containing content you want summarized'


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
    args = parser.parse_args()
    run_bill_getting_pipeline(args.secrets_file, args.months)


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
    args = parser.parse_args()
    run_summarize_pipeline(args.secrets_file, args.text_file)
