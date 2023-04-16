"""
This file contains functions that map to programs that can be called
from the command line upon installing the accountability pip package.
This should just map command line arguments to parameters passed into functions
See entry_points in setup.py
"""

import argparse
from accountability.pipelines import run_main_pipeline, run_setup_pipeline


def run():
    parser = argparse.ArgumentParser(
        description='Run main entrypoint')
    parser.add_argument('secrets_file', help='yaml file containing secrets needed for this program')
    parser.add_argument('-m', '--months', type=int, default=6)
    args = parser.parse_args()
    run_main_pipeline(args.secrets_file, args.months)


def setup():
    parser = argparse.ArgumentParser(
        description='Create a template yaml file for storing secrets')
    parser.add_argument('-t', '--template', default='template.yaml')
    args = parser.parse_args()
    run_setup_pipeline(args.template)
