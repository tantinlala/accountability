from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import TextLoader
from langchain_openai import OpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate
import textwrap

class Summarizer:
    SECRET_GROUP = 'openai'
    KEY_NAME = 'OPENAI_API_KEY'

    BILL_MAP_PROMPT = textwrap.dedent("""
    You are an expert analyst specializing in legislative summaries. Given the following passage from a US Congress bill, please:

	1. Provide a concise summary of the key points in this passage.
    2. Identify and explain any potential impacts or implications these points may have on middle-class Americans, focusing on economic, social, and legal aspects.
    """)

    BILL_DIFFS_PROMPT = "Summarize the following diffs between bills for a layperson."

    BILL_COMBINE_PROMPT = textwrap.dedent("""
    As a legislative summary expert, please synthesize the following summaries and impact assessments into a comprehensive overview of the US Congress bill. Your summary should:

	1. Highlight the main objectives and provisions of the bill.
    2. Provide an integrated analysis of the potential impacts on middle-class Americans, consolidating specific effects identified in the summaries that follow.
    """)

    def __init__(self, secrets_parser):
        self.api_key_ = secrets_parser.get_secret(self.SECRET_GROUP, self.KEY_NAME)


    def _summarize_file(self, filepath, map_prompt, combine_prompt):

        # Step 1: Load Your Text Data
        loader = TextLoader(filepath)
        documents = loader.load()

        # Step 2: Split the Text for Better Handling
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            separators=["\n\n", "\n", " ", ""]
        )
        docs = text_splitter.split_documents(documents)

        print(f"Summarizing {filepath}")

        map_prompt = PromptTemplate.from_template(
            map_prompt + "\n\n{text}"
        )

        combine_prompt = PromptTemplate.from_template(
            combine_prompt + "\n\n{text}"
        )

        # Step 5: Set Up the Summarization Chain
        llm = OpenAI(api_key=self.api_key_, temperature=0.7)  # You can adjust temperature for more or less creativity
        chain = load_summarize_chain(llm, chain_type="map_reduce", map_prompt=map_prompt, combine_prompt=combine_prompt, combine_document_variable_name="text", map_reduce_document_variable_name="text")

        # Step 6: Run the Summarization Chain on the Documents
        summary = chain.run(input_documents=docs)

        return summary


    def summarize_bill(self, filepath):
        return self._summarize_file(filepath, self.BILL_MAP_PROMPT, self.BILL_COMBINE_PROMPT)


    def summarize_bill_diffs(self, filepath):
        return self._summarize_file(filepath, self.BILL_DIFFS_PROMPT, self.BILL_DIFFS_PROMPT)
