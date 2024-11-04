from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import TextLoader
from langchain_openai import ChatOpenAI
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate
import textwrap

class Summarizer:
    SECRET_GROUP = 'openai'
    KEY_NAME = 'OPENAI_API_KEY'

    BILL_MAP_PROMPT = textwrap.dedent("""
    You are an expert analyst specializing in legislative summaries. Given the following passage from a US Congress bill, please 
	provide a concise summary of the key objectives in this passage.
    """)

    BILL_DIFFS_PROMPT = "Summarize the following diffs between bills for a layperson."

    BILL_COMBINE_PROMPT = textwrap.dedent("""
    As a legislative summary expert, please synthesize the following summaries and impact assessments into a comprehensive overview of the US Congress bill. Your summary should
	highlight the main objectives and provisions of the bill in layman's terms.
    """)

    def __init__(self, secrets_parser):
        self.api_key_ = secrets_parser.get_secret(self.SECRET_GROUP, self.KEY_NAME)


    def _map_reduce_file(self, filepath, map_prompt, combine_prompt):

        # Step 1: Load Your Text Data
        loader = TextLoader(filepath)
        documents = loader.load()

        # Step 2: Split the Text for Better Handling
        text_splitter = CharacterTextSplitter.from_tiktoken_encoder(chunk_size=1000, chunk_overlap=0)
        docs = text_splitter.split_documents(documents)

        print(f"Summarizing {filepath}")

        map_prompt = PromptTemplate.from_template(
            map_prompt + "\nBILL PASSAGE:\n{text}\nSUMMARY:"
        )

        combine_prompt = PromptTemplate.from_template(
            combine_prompt + "\nSUMMARIES:\n{text}\nFINAL SUMMARY:"
        )

        # Step 5: Set Up the Summarization Chain
        llm = ChatOpenAI(api_key=self.api_key_, model='gpt-4o', temperature=0, max_tokens=None, timeout=None, max_retries=2)  # You can adjust temperature for more or less creativity
        chain = load_summarize_chain(llm, chain_type="map_reduce", map_prompt=map_prompt, combine_prompt=combine_prompt, combine_document_variable_name="text", map_reduce_document_variable_name="text")

        # Step 6: Run the Summarization Chain on the Documents
        summary = chain.run(input_documents=docs)

        # Remove leading and trailing whitespace
        if summary is not None:
            summary = summary.strip()

        return summary


    def summarize_bill(self, filepath):
        return self._map_reduce_file(filepath, self.BILL_MAP_PROMPT, self.BILL_COMBINE_PROMPT)


    def summarize_bill_diffs(self, filepath):
        return self._map_reduce_file(filepath, self.BILL_DIFFS_PROMPT, self.BILL_DIFFS_PROMPT)

