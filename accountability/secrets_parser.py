import yaml


class SecretsParser:
    def __init__(self):
        self.parsed_secrets_dict_ = None
        self.template_secrets_dict_ = dict()

    # Get a dictionary of secrets from a yaml file
    def parse_secrets_file(self, secrets_file):
        with open(secrets_file, 'r') as file:
            self.parsed_secrets_dict_ = yaml.safe_load(file)

    # Save a template yaml file based on secrets that clients requested via get_secret
    def create_template_secrets_file(self, secrets_file):
        with open(secrets_file, 'w') as file:
            yaml.dump(self.template_secrets_dict_, file)

    def get_secret(self, service_name, secret_name):
        # Build up a template secrets dictionary based on client's requests
        if service_name not in self.template_secrets_dict_.keys():
            self.template_secrets_dict_[service_name] = dict()
        self.template_secrets_dict_[service_name][secret_name] = ""

        # Get secret if available. Depends on having previously parsed secrets file
        try:
            secret = self.parsed_secrets_dict_[service_name][secret_name]
        except TypeError:
            secret = ""

        return secret

