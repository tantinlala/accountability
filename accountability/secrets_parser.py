import yaml


class SecretsParser:
    def __init__(self):
        self.parsed_secrets_dict_ = None
        self.template_secrets_dict_ = dict()

    def parse_secrets_file(self, existing_secrets_file):
        """
        Get a dictionary of secrets from a yaml file
        :param existing_secrets_file: yaml file containing groups of (name : secret) value pairs
        """
        with open(existing_secrets_file, 'r') as file:
            self.parsed_secrets_dict_ = yaml.safe_load(file)

    def create_template_secrets_file(self, template_secrets_file):
        """
        Save a template yaml file based on secrets that clients requested via get_secret
        :param template_secrets_file: yaml file to save containing a template of what secrets need to be filled in
        """
        with open(template_secrets_file, 'w') as file:
            yaml.dump(self.template_secrets_dict_, file)

    def get_secret(self, service_name, secret_name):
        """
        Get secret from dictionary parsed from secrets file. parse_secrets_file needs to have been called first
        :param service_name: The name of a service to which the secret belongs (e.g. a certain web API)
        :param secret_name: The name of the secret (e.g. "API_KEY")
        :return: String representing the secret (e.g. an API key)
        """

        # Build up a template secrets dictionary based on client's requests
        # This is used to eventually create a template yaml file upon calling create_template_secrets_file
        if service_name not in self.template_secrets_dict_.keys():
            self.template_secrets_dict_[service_name] = dict()
        self.template_secrets_dict_[service_name][secret_name] = ""

        # Try getting the secret from the dictionary generated in parse_secrets_file
        try:
            secret = self.parsed_secrets_dict_[service_name][secret_name]
        except TypeError:
            secret = None
        except KeyError:
            secret = None

        return secret
