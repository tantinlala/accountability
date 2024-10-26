"""
This file contains functions that map to programs that can be called
from the command line upon installing the accountability pip package.
This should just map command line arguments to parameters passed into functions in pipelines.py
See entry_points in setup.py
"""

import argparse
from accountability.runners import run_setup, run_summarize_bill, run_process_hr_rollcalls, run_get_bill, run_get_amendment


SECRETS_FILE_HELP_STRING = 'Yaml file containing secrets needed for this program'
TEXT_FILE_HELP_STRING = 'Text file containing content you want summarized'
SAVE_DIRECTORY_HELP_STRING = 'Directory to which you want to save file'


def setup():
    parser = argparse.ArgumentParser(
        description='Create a template yaml file for storing secrets (e.g. api keys)')
    parser.add_argument('-t', '--template', default='template.yaml')
    parser.add_argument('-r', '--roll_call_id', type=int, default=0, help='The roll call ID to store in the database')
    args = parser.parse_args()
    run_setup(args.template, args.roll_call_id)


def get_bill():
    parser = argparse.ArgumentParser(
        description='Print the text of a bill')
    parser.add_argument('-s', '--secrets_file', help=SECRETS_FILE_HELP_STRING, default='secrets.yaml')
    parser.add_argument('-c', '--congress', help='Congress number')
    parser.add_argument('-b', '--bill_id', help='The bill id for which you want to get text')
    parser.add_argument('-t', '--datetime', help='The datetime of the bill action')
    parser.add_argument('-d', '--save_directory', help=SAVE_DIRECTORY_HELP_STRING, default='results')
    args = parser.parse_args()
    run_get_bill(args.secrets_file, args.congress, args.bill_id, args.datetime, args.save_directory)


def get_amendment():
    parser = argparse.ArgumentParser(
        description='Print the amendments for a bill')
    parser.add_argument('-s', '--secrets_file', help=SECRETS_FILE_HELP_STRING, default='secrets.yaml')
    parser.add_argument('-c', '--congress', help='Congress number')
    parser.add_argument('-b', '--bill_id', help='The bill id for which you want to get amendments')
    parser.add_argument('-t', '--datetime', help='The datetime of the bill action')
    parser.add_argument('-d', '--save_directory', help=SAVE_DIRECTORY_HELP_STRING, default='results')
    args = parser.parse_args()
    run_get_amendment(args.secrets_file, args.congress, args.bill_id, args.datetime, args.save_directory)


def summarize_bill():
    parser = argparse.ArgumentParser(
        description='Summarize a text document')
    parser.add_argument('-s', '--secrets_file', help=SECRETS_FILE_HELP_STRING, default='secrets.yaml')
    parser.add_argument('-t', '--text_file', help=TEXT_FILE_HELP_STRING)
    parser.add_argument('-d', '--save_directory', help=SAVE_DIRECTORY_HELP_STRING, default='results')
    args = parser.parse_args()
    run_summarize_bill(args.secrets_file, args.text_file, args.save_directory)


def process_hr_rollcalls():
    parser = argparse.ArgumentParser(
        description='Download the text of the most recently voted upon HR bill')
    parser.add_argument('-s', '--secrets_file', help=SECRETS_FILE_HELP_STRING, default='secrets.yaml')
    parser.add_argument('-d', '--save_directory', help=SAVE_DIRECTORY_HELP_STRING, default='results')
    args = parser.parse_args()
    run_process_hr_rollcalls(args.secrets_file, args.save_directory)
