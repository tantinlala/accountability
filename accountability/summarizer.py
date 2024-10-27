import os

class Summarizer:
    def __init__(self, assistant):
        self.assistant_ = assistant


    def summarize_bill(self, filepath):
        """
        Uses an AI model to summarize the contents of a .txt file. Writes the summary to a new text file
        :param filename: Name of .txt file to summarize
        """

        file_id = self.assistant_.create_file(filepath)

        prompt = "Summarize the following bill for a layperson in terms of how it may impact the average American. \
        Bullet point each key point. For each key point, provide a section number from within the bill I provided where one \
        can find more information about that point."

        print(f"Summarizing {filepath}")

        summary = self.assistant_.prompt_with_file(prompt, file_id)
        self.assistant_.delete_file(file_id)
        return summary


    def summarize_bill_diffs(self, save_directory, filepath):
        """
        Uses an AI model to summarize the differences between two versions of a bill. Writes the summary to a new text file
        :param diff_string: String containing the differences between two versions of a bill
        :param save_directory: Directory to save the diff summary file
        """
        summary_filepath = self.make_summary_filepath(save_directory, filepath)

        if os.path.exists(summary_filepath):
            print(f"Skipping summary for {summary_filepath} because it already exists")
            return

        file_id = self.assistant_.create_file(filepath)

        prompt = "Summarize the diffs for a bill provided in the attached file for a layperson"

        print(f"Summarizing {filepath}")

        summary = self.assistant_.prompt_with_file(prompt, file_id)
        self.assistant_.delete_file(file_id)

        if summary:
            with open(summary_filepath, 'w') as summary_file:
                summary_file.write(summary)
