import os
import tiktoken
from langchain.chains.summarize import load_summarize_chain
from langchain.text_splitter import TokenTextSplitter
from langchain.docstore.document import Document
from langchain.llms import OpenAI


class Summarizer:
    SECRET_GROUP = 'openai'
    SECRET_NAME = 'OPENAI_API_KEY'
    MODEL_NAME = "text-davinci-003"
    CHAIN_TYPE = "map_reduce"
    CHUNK_SIZE = 3500  # Make room for summarization prompt

    def __init__(self, secrets_parser):
        self.secret = secrets_parser.get_secret(self.SECRET_GROUP, self.SECRET_NAME)
        os.environ[self.SECRET_NAME] = self.secret

        self.encoding_ = tiktoken.encoding_for_model(self.MODEL_NAME)

    def summarize_file(self, filename):
        with open(filename, 'r') as text_file:
            full_text = text_file.read()

        text_splitter = TokenTextSplitter(encoding_name=self.encoding_.name, chunk_size=self.CHUNK_SIZE)
        texts = text_splitter.split_text(full_text)
        docs = list()
        for text in texts:
            docs.append(Document(page_content=text))

        llm = OpenAI(model_name=self.MODEL_NAME)
        chain = load_summarize_chain(llm, self.CHAIN_TYPE)
        summary = chain.run(docs)

        base_filename = os.path.split(filename)
        summary_filename = 'summary-' + base_filename[1]
        with open(summary_filename, 'w') as summary_file:
            summary_file.write(summary)

    def calculate_tokens_for_file(self, filename):
        with open(filename, 'r') as file:
            text = file.read()
            num_tokens = len(self.encoding_.encode(text))
            print(filename + ": " + str(num_tokens))
