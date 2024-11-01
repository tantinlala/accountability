import os
from accountability.file_utils import make_summary_filepath, get_previous_version_file, get_diff, save_if_not_exists, file_exists

class Reporter:

    def __init__(self, summarizer):
        self.summarizer_ = summarizer
        self.summary_filepath = None

    def add_summary_filepath(self, summary_filepath):
        self.summary_filepath = summary_filepath

    def write_rollcall_report(self, rollcall_id, year, congress_db, bill_folder_string):

        # TODO: handle amendment
        # TODO: check whether there was a previous vote on this amendment and find all of the changes in votes?
        # TODO: add data related to amendment to report

        rollcall_data = congress_db.get_rollcall_data(rollcall_id, year)
        bill_filename = rollcall_data['BillName']
        bill_filepath = os.path.join(bill_folder_string, bill_filename)
        if not bill_filepath.endswith('.txt'):
            bill_filepath += '.txt'
        amendment_filename = rollcall_data['AmendmentName']

        summary = None
        if previous_version_filepath := get_previous_version_file(bill_filepath):
            diff_text = get_diff(bill_filepath, previous_version_filepath)
            diff_filepath = save_if_not_exists(bill_folder_string, bill_filename + "-diffs", diff_text)
            if file_exists(diff_summary_filepath := make_summary_filepath(diff_filepath)):
                print(f"Skipping summary because {diff_summary_filepath} already exists")
                summary = open(diff_summary_filepath).read()
            elif os.path.getsize(diff_filepath) == 0:
                print(f"Skipping summary because {diff_filepath} is empty")
            elif summary := self.summarizer_.summarize_bill_diffs(diff_filepath):
                with open(diff_summary_filepath, 'w') as summary_file:
                    summary_file.write(summary)

        else: # No previous version
            if file_exists(bill_summary_filepath := make_summary_filepath(bill_filepath)):
                print(f"Skipping summary because {bill_summary_filepath} already exists")
                summary = open(bill_summary_filepath).read()
            elif summary := self.summarizer_.summarize_bill(bill_filepath):
                with open(bill_summary_filepath, 'w') as summary_file:
                    summary_file.write(summary)


        # Save information on the rollcall to an .md file
        datetime_string = rollcall_data['ActionDateTime']
        rollcall_file = f"{bill_folder_string}/{datetime_string}-rollcall-{rollcall_id}.md"

        previous_rollcall_data = congress_db.get_previous_rollcall_data(rollcall_id, year, rollcall_data['Question'])
        previous_votes = {vote['CongressmanID']: vote['Vote'] for vote in previous_rollcall_data['Votes']} if previous_rollcall_data else {}

        with open(rollcall_file, 'w') as file:
            # Get file name from file path
            file.write(f"Roll Call Time: {datetime_string}\n\n")
            file.write(f"Vote Question: {rollcall_data['Question']}\n\n")
            file.write(f"Bill Version File: {bill_filename}\n\n")
            if amendment_filename is not None:
                file.write(f"Amendment File: {amendment_filename}\n\n")

            # Loop through each vote and write to the file as a markdown table
            # Each vote has the following format {'name': name, 'party': party, 'state': state, 'vote': vote_type}
            file.write("| Name | Party | State | Vote | Previous Vote |\n")
            file.write("|------|-------|-------|------|---------------|\n")
            for vote in rollcall_data['Votes']:
                previous_vote = previous_votes.get(vote['CongressmanID'], 'N/A')
                file.write(f"| {vote['Name']} | {vote['Party']} | {vote['State']} | {vote['Vote']} | {previous_vote} |\n")

            if summary:
                file.write("\n\nSummary:\n")
                file.write(summary)

        print(f"Saved votes for {rollcall_id} to {rollcall_file}")
