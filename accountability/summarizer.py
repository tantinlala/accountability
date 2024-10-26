import os

class Summarizer:
    def __init__(self, assistant, filename):
        self.assistant_ = assistant
        self.filename_ = filename

        # Get base filename without extension
        self.base_filename_ = os.path.split(filename)
        self.base_filename_ = os.path.splitext(self.base_filename_[1])
        self.base_filename_ = self.base_filename_[0]

    def summarize_bill(self, save_directory):
        """
        Uses an AI model to summarize the contents of a .txt file. Writes the summary to a new text file
        :param filename: Name of .txt file to summarize
        """

        if save_directory[-1] != '/':
            save_directory = save_directory + '/'
        summary_filename = save_directory + self.base_filename_ + '-summary.md'

        if os.path.exists(summary_filename):
            print(f"Skipping summary because {summary_filename} already exists")
            return

        file_id = self.assistant_.create_file(self.filename_)

        prompt = "Summarize the following bill for a layperson in terms of how it may impact the average American. \
        Bullet point each key point. For each key point, provide a section number from within the bill I provided where one \
        can find more information about that point."

        summary = self.assistant_.prompt_with_file(prompt, file_id)
        self.assistant_.delete_file(file_id)

        if summary:
            with open(summary_filename, 'w') as summary_file:
                summary_file.write(summary)

    def summarize_file_diffs(self, diff_string, save_directory):
        """
        Uses an AI model to summarize the differences between two versions of a bill. Writes the summary to a new text file
        :param diff_string: String containing the differences between two versions of a bill
        :param save_directory: Directory to save the diff summary file
        """

        if save_directory[-1] != '/':
            save_directory = save_directory + '/'
        diff_summary_filename = save_directory + self.base_filename_ + '-diffs.md'

        if os.path.exists(diff_summary_filename):
            print(f"Skipping summary for {diff_summary_filename} because it already exists")
            return

        file_id = self.assistant_.create_file(self.filename_)

        prompt = "Summarize the following diffs that are applied on top of the original version of the bill for a layperson: \n" + diff_string

        summary = self.assistant_.prompt_with_file(prompt, file_id)

        if summary:
            with open(diff_summary_filename, 'w') as diff_summary_file:
                diff_summary_file.write(summary)
