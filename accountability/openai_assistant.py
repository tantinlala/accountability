from openai import OpenAI

class OpenAIAssistant:
    SECRET_GROUP = 'openai'
    KEY_NAME = 'OPENAI_API_KEY'
    ASSISTANT_NAME = "ASSISTANT_ID"
    MODEL_NAME = "gpt-4o"

    def __init__(self, secrets_parser=None):
        self.api_key_ = secrets_parser.get_secret(self.SECRET_GROUP, self.KEY_NAME)
        self.assistant_id_ = secrets_parser.get_secret(self.SECRET_GROUP, self.ASSISTANT_NAME)

        self.client_ = None
        if self.api_key_ is not None:
            self.client_ = OpenAI(api_key=self.api_key_)

    def create_file(self, filename):
        message_file = self.client_.files.create(file=open(filename, "rb"), purpose="assistants")
        return message_file.id

    def delete_file(self, file_id):
        self.client_.files.delete(file_id)

    def prompt_with_file(self, prompt, file_id):
        thread = self.client_.beta.threads.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                    "attachments": [
                        {"file_id": file_id, "tools": [{"type": "file_search"}]}
                    ],
                }
            ]
        )

        run = self.client_.beta.threads.runs.create_and_poll(
                thread_id=thread.id, assistant_id=self.assistant_id_)

        messages = list(self.client_.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))

        message_content = messages[0].content[0].text
        annotations = message_content.annotations

        for annotation in annotations:
            message_content.value = message_content.value.replace(annotation.text, "")

        summary = message_content.value

        return summary