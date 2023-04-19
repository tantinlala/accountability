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
    MODEL_COST_1000TK = .02
    CHAIN_TYPE = "map_reduce"
    CHUNK_SIZE = 3500  # Make room for summarization prompt

    def __init__(self, secrets_parser=None, api_key=None):
        if secrets_parser is not None:
            api_key = secrets_parser.get_secret(self.SECRET_GROUP, self.SECRET_NAME)

        if api_key is not None:
            self.llm = OpenAI(temperature=0.0, openai_api_key=api_key, model_name=self.MODEL_NAME)

        self.encoding_ = tiktoken.encoding_for_model(self.MODEL_NAME)

    def summarize_file(self, filename, save_directory):
        """
        Uses an AI model to summarize the contents of a .txt file. Writes the summary to a new text file
        :param filename: Name of .txt file to summarize
        """
        with open(filename, 'r') as text_file:
            full_text = text_file.read()

        text_splitter = TokenTextSplitter(encoding_name=self.encoding_.name, chunk_size=self.CHUNK_SIZE)
        texts = text_splitter.split_text(full_text)
        docs = list()
        for text in texts:
            docs.append(Document(page_content=text))

        chain = load_summarize_chain(self.llm, self.CHAIN_TYPE)
        summary = chain.run(docs)

        base_filename = os.path.split(filename)
        if save_directory[-1] != '/':
            save_directory = save_directory + '/'
        summary_filename = save_directory + 'summary-' + base_filename[1]
        with open(summary_filename, 'w') as summary_file:
            summary_file.write(summary)
            print("\n" + summary, end="\n")

    def print_estimated_cost_of_file_summary(self, filename):
        """
        Estimates the cost of summarizing a .txt file and prints the cost
        :param filename: Name of .txt file to summarize
        """
        with open(filename, 'r') as file:
            text = file.read()
            num_tokens = len(self.encoding_.encode(text))
            cost = num_tokens * self.MODEL_COST_1000TK / 1000.0
            print(filename + " : ${:.2f}".format(cost))
