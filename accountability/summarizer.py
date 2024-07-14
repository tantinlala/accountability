import os
import tiktoken
from openai import OpenAI


class Summarizer:
    SECRET_GROUP = 'openai'
    KEY_NAME = 'OPENAI_API_KEY'
    ASSISTANT_NAME = "ASSISTANT_ID"
    MODEL_NAME = "gpt-4o"
    MODEL_COST_1000000TK = 5
    MAX_NUM_CHARS_PER_LINE = 80

    def __init__(self, secrets_parser=None, api_key=None):
        if secrets_parser is not None:
            self.api_key_ = secrets_parser.get_secret(self.SECRET_GROUP, self.KEY_NAME)
            self.assistant_id_ = secrets_parser.get_secret(self.SECRET_GROUP, self.ASSISTANT_NAME)

        self.encoding_ = tiktoken.encoding_for_model(self.MODEL_NAME)

    def summarize_file(self, filename, save_directory):
        """
        Uses an AI model to summarize the contents of a .txt file. Writes the summary to a new text file
        :param filename: Name of .txt file to summarize
        """
        with open(filename, 'r') as text_file:
            full_text = text_file.read()

        prompt = "Summarize the following bill for a layperson in terms of how it may impact the average American"

        client = OpenAI(api_key=self.api_key_)
        message_file = client.files.create(
            file=open(filename, "rb"), purpose="assistants")

        thread = client.beta.threads.create(
          messages=[
            {
              "role": "user",
              "content": prompt,
              # Attach the new file to the message.
              "attachments": [
                { "file_id": message_file.id, "tools": [{"type": "file_search"}] }
              ],
            }
          ]
        )

        run = client.beta.threads.runs.create_and_poll(
                thread_id=thread.id, assistant_id=self.assistant_id_)

        messages = list(client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))

        summary = messages[0].content[0].text.value
        words = summary.split()
        lines = []
        current_line = ""
        for word in words:
            if len(current_line) + len(word) > self.MAX_NUM_CHARS_PER_LINE:
                lines.append(current_line.strip())
                current_line = word + " "
            else:
                current_line += word + " "

        lines.append(current_line.strip())
        summary = "\n".join(lines)

        base_filename = os.path.split(filename)
        if save_directory[-1] != '/':
            save_directory = save_directory + '/'
        summary_filename = save_directory + 'summary-' + base_filename[1]
        with open(summary_filename, 'w') as summary_file:
            summary_file.write(summary)

    def print_estimated_cost_of_file_summary(self, filename):
        """
        Estimates the cost of summarizing a .txt file and prints the cost
        :param filename: Name of .txt file to summarize
        """
        with open(filename, 'r') as file:
            text = file.read()
            num_tokens = len(self.encoding_.encode(text))
            cost = num_tokens * self.MODEL_COST_1000000TK / 1000000.0
            print(filename)
            print("Number of tokens: {}".format(num_tokens))
            print("Cost: ${:.2f}".format(cost))
