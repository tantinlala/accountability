class Summarizer:
    SECRET_GROUP = 'openai'
    SECRET_NAME = 'OPENAI_API_KEY'

    def __init__(self, secrets_parser):
        self.secret = secrets_parser.get_secret(self.SECRET_GROUP, self.SECRET_NAME)

