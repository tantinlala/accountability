import yaml
import argparse


def authenticate(authentication_file):
    with open(authentication_file, 'r') as auth_file:
        auth_dict = yaml.safe_load(auth_file)
        print(auth_dict['openai']['OPENAI_API_KEY'])


def run():
    parser = argparse.ArgumentParser(
        prog='Run main entrypoint')
    parser.add_argument('authentication_file')  # positional argument
    args = parser.parse_args()
    authenticate(args.authentication_file)
