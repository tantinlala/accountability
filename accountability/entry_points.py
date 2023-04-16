"""
This file contains functions that map to programs that can be called
from the command line upon installing the accountability pip package.
This should just map command line arguments to parameters passed into functions
See entry_points in setup.py
"""

import argparse
from accountability.pipelines import run_bill_getting_pipeline, run_setup_pipeline, \
    run_summarize_pipeline, run_calculate_tokens_pipeline

SECRETS_FILE_HELP_STRING = 'Yaml file containing secrets needed for this program'


def calc_tokens():
    parser = argparse.ArgumentParser(
        description='Calculate number of tokens in a text document')
    parser.add_argument('-t', '--text_file', help='Text file containing content you want number of tokens for')
    args = parser.parse_args()
    run_calculate_tokens_pipeline(args.text_file)


def summarize():
    parser = argparse.ArgumentParser(
        description='Summarize a text document')
    parser.add_argument('-s', '--secrets_file', help=SECRETS_FILE_HELP_STRING)
    parser.add_argument('-t', '--text_file', help='Text file containing content you want summarized')
    args = parser.parse_args()
    run_summarize_pipeline(args.secrets_file, args.text_file)


def get_senate_bills():
    parser = argparse.ArgumentParser(
        description='Download text of bills voted upon within past months')
    parser.add_argument('-s', '--secrets_file', help=SECRETS_FILE_HELP_STRING)
    parser.add_argument('-m', '--months', type=int, default=6)
    args = parser.parse_args()
    run_bill_getting_pipeline(args.secrets_file, args.months)


def setup():
    parser = argparse.ArgumentParser(
        description='Create a template yaml file for storing secrets')
    parser.add_argument('-t', '--template', default='template.yaml')
    args = parser.parse_args()
    run_setup_pipeline(args.template)
