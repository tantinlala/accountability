import yaml


def run():
    AUTHENTICATION_FILE = 'auth.yaml'
    with open(AUTHENTICATION_FILE, 'r') as auth_file:
        auth_dict = yaml.safe_load(auth_file)
        print(auth_dict['openai']['OPENAI_API_KEY'])
