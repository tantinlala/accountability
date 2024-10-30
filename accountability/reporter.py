import os
from accountability.file_utils import make_summary_filepath, get_previous_version_file, get_diff, save_if_not_exists, file_exists


class Reporter:

    def __init__(self, summarizer):
        self.summarizer_ = summarizer
        self.summary_filepath = None

    def add_summary_filepath(self, summary_filepath):
        self.summary_filepath = summary_filepath

    def write_rollcall_report(self, rollcall_id, year, congress_db, bill_filepath, amendment_filepath, save_directory):

        # TODO: handle amendment
        # TODO: check whether there was a previous vote on this amendment and find all of the changes in votes?
        # TODO: add data related to amendment to report

        bill_filename = os.path.basename(bill_filepath).split(".")[0]
        amendment_filename = os.path.basename(amendment_filepath).split(".")[0] if amendment_filepath else None

        summary = None

        if previous_version_filepath := get_previous_version_file(bill_filepath):
            diff_text = get_diff(bill_filepath, previous_version_filepath)
            diff_filepath = save_if_not_exists(save_directory, bill_filename + "-diffs", diff_text)
            if file_exists(diff_summary_filepath := make_summary_filepath(diff_filepath)):
                print(f"Skipping summary because {diff_summary_filepath} already exists")
            elif summary := self.summarizer_.summarize_bill_diffs(diff_filepath):
                with open(diff_summary_filepath, 'w') as summary_file:
                    summary_file.write(summary)

        else: # No previous version
            if file_exists(bill_summary_filepath := make_summary_filepath(bill_filepath)):
                print(f"Skipping summary because {bill_summary_filepath} already exists")
            elif summary := self.summarizer_.summarize_bill(bill_filepath):
                with open(bill_summary_filepath, 'w') as summary_file:
                    summary_file.write(summary)


        # Save information on the rollcall to an .md file
        # Create file path for roll call
        rollcall_data = congress_db.get_rollcall_data(rollcall_id, year)
        datetime_string = rollcall_data['ActionDateTime']
        rollcall_file = f"{save_directory}/{datetime_string}-rollcall-{rollcall_id}.md"

        with open(rollcall_file, 'w') as file:
            # Get file name from file path
            file.write(f"Roll Call Time: {datetime_string}\n\n")
            file.write(f"Vote Question: {rollcall_data['Question']}\n\n")
            file.write(f"Bill Version File: {bill_filename}\n\n")
            if amendment_filename is not None:
                file.write(f"Amendment File: {amendment_filename}\n\n")

            # Loop through each vote and write to the file as a markdown table
            # Each vote has the following format {'name': name, 'party': party, 'state': state, 'vote': vote_type}
            file.write("| Name | Party | State | Vote |\n")
            file.write("|------|-------|-------|------|\n")
            for vote in rollcall_data['Votes']:
                file.write(f"| {vote['Name']} | {vote['Party']} | {vote['State']} | {vote['Vote']} |\n")

        print(f"Saved votes for {rollcall_id} to {rollcall_file}")

        # TODO: check whether there was a previous vote for the same question and find all of the changes in votes?
        # TODO: create report specific to diffs in versions and votes
