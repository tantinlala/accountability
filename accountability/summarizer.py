import os

class Summarizer:
    BILL_PROMPT = "Summarize the following bill for a layperson in terms of how it may impact the average American. \
    Bullet point each key point. For each key point, provide a section number from within the bill I provided where one \
    can find more information about that point."

    BILL_DIFFS_PROMPT = "Summarize the diffs for a bill provided in the attached file for a layperson"

    def __init__(self, assistant):
        self.assistant_ = assistant


    def _summarize_file(self, filepath, prompt):
        file_id = self.assistant_.create_file(filepath)

        print(f"Summarizing {filepath}")

        summary = self.assistant_.prompt_with_file(prompt, file_id)
        self.assistant_.delete_file(file_id)
        return summary


    def summarize_bill(self, filepath):
        return self._summarize_file(filepath, self.BILL_PROMPT)


    def summarize_bill_diffs(self, filepath):
        return self._summarize_file(filepath, self.BILL_DIFFS_PROMPT)
