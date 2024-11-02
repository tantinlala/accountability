from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import TextLoader
from langchain_openai import OpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate

class Summarizer:
    SECRET_GROUP = 'openai'
    KEY_NAME = 'OPENAI_API_KEY'

    BILL_MAP_PROMPT = "Summarize the following bill for a layperson in terms of how it may impact the average American. \
    Bullet point each key point. For each key point, provide a section number from within the bill I provided where one \
    can find more information about that point: \n"

    BILL_DIFFS_MAP_PROMPT = "Summarize the diffs for a bill provided in the attached file for a layperson: \n"

    COMBINE_PROMPT = "You have been provided with a list of summaries. Please combine them into a final, comprehensive summary: \n"

    def __init__(self, secrets_parser):
        self.api_key_ = secrets_parser.get_secret(self.SECRET_GROUP, self.KEY_NAME)


    def _summarize_file(self, filepath, map_prompt):

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

        # Step 3: Create Embeddings Using OpenAI
        # Use the API key from the secrets parser
        embeddings = OpenAIEmbeddings(api_key=self.api_key_)

        # Step 4: Set Up Chroma as the Vector Store
        vector_store = Chroma.from_documents(docs, embeddings)

        print(f"Summarizing {filepath}")

        map_prompt = PromptTemplate.from_template(
            """
            You are an expert summarizer. Please provide a concise summary of the following text:

            {text}
            """
        )

        combine_prompt = PromptTemplate.from_template(
            """
            You have been provided with a list of summaries. Please combine them into a final, comprehensive summary:

            {text}
            """
        )

        # Step 5: Set Up the Summarization Chain
        llm = OpenAI(api_key=self.api_key_, temperature=0.7)  # You can adjust temperature for more or less creativity
        chain = load_summarize_chain(llm, chain_type="map_reduce", map_prompt=map_prompt, combine_prompt=combine_prompt, combine_document_variable_name="text", map_reduce_document_variable_name="text")

        # Step 6: Run the Summarization Chain on the Documents
        summary = chain.run(input_documents=docs)

        return summary


    def summarize_bill(self, filepath):
        return self._summarize_file(filepath, self.BILL_MAP_PROMPT)


    def summarize_bill_diffs(self, filepath):
        return self._summarize_file(filepath, self.BILL_DIFFS_MAP_PROMPT)
