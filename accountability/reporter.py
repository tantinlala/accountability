import os
from accountability.file_utils import make_summary_filepath, make_txt_filepath, get_diff, save_txt_if_not_exists, file_exists, make_dated_filename

class Reporter:

    def __init__(self, summarizer, industry_classifier, congress_db):
        self.summarizer_ = summarizer
        self.industry_classifier_ = industry_classifier
        self.congress_db_ = congress_db
        self.summary_filepath = None


    def generate_summary(self, present_rollcall_data, previous_rollcall_data, bill_folder_string):
        bill_name = present_rollcall_data['BillName']
        bill_datetime = present_rollcall_data['BillDateTime']
        dated_bill_name = make_dated_filename(bill_datetime, bill_name)
        bill_filepath = make_txt_filepath(bill_folder_string, dated_bill_name)

        summary = None

        # Previous rollcall related to same bill, question, and amendment exists,
        # but the bill version changed between rollcalls
        if (previous_rollcall_data is not None) and \
            (bill_name != previous_rollcall_data['BillName']):
            previous_version_bill_name = previous_rollcall_data['BillName']
            previous_version_bill_datetime = previous_rollcall_data['BillDateTime']
            previous_version_dated_bill_name = make_dated_filename(previous_version_bill_datetime, previous_version_bill_name)
            previous_version_bill_filepath = make_txt_filepath(bill_folder_string, previous_version_dated_bill_name)

            diff_string = get_diff(bill_filepath, previous_version_bill_filepath)

            diff_filepath = save_txt_if_not_exists(bill_folder_string, f"{dated_bill_name}-diffs", diff_string)
            if file_exists(summary_filepath := make_summary_filepath(diff_filepath)):
                print(f"Skipping summary because {summary_filepath} already exists")
                summary = open(summary_filepath).read()
            elif os.path.getsize(diff_filepath) == 0:
                print(f"Skipping summary because {diff_filepath} is empty")
                summary = "" # TODO: get summary for previous version instead
            elif summary := self.summarizer_.summarize_bill_diffs(diff_filepath):
                with open(summary_filepath, 'w') as summary_file:
                    summary_file.write(summary)
            else:
                print(f"Failed to summarize diffs for {diff_filepath}")
                summary = "No summary available for diffs"
            summary = f"# Summary of Diffs Between {bill_name} and {previous_version_bill_name}:\n{summary}"
        # TODO: check whether there was a previous vote on this amendment and find all of the changes in votes?
        else:
            if file_exists(summary_filepath := make_summary_filepath(bill_filepath)):
                print(f"Skipping summary because {summary_filepath} already exists")
                summary = open(summary_filepath).read()
            elif summary := self.summarizer_.summarize_bill(bill_filepath):
                with open(summary_filepath, 'w') as summary_file:
                    summary_file.write(summary)
                # Classify the bill summary and add bill-industry pairs to the database
                classification_results = self.industry_classifier_.classify(summary)
                for industry_code in classification_results.industry_codes:
                    self.congress_db_.add_bill_industry(present_rollcall_data['BillName'], industry_code)
            else:
                print(f"Failed to summarize {bill_filepath}")
                summary = "No summary available for bill"
            summary = f"# Bill Summary\n{summary}"

        return summary


    def write_rollcall_report(self, rollcall_id, year, save_directory, bill_folder_string):
        rollcall_data = self.congress_db_.get_rollcall_data(rollcall_id, year)
        previous_rollcall_data = self.congress_db_.get_previous_rollcall_data(rollcall_id, year)

        summary = self.generate_summary(rollcall_data, previous_rollcall_data, bill_folder_string)

        datetime_string = rollcall_data['ActionDateTime']

        # Create {save_directory}/rollcalls directory if it doesn't exist
        if not os.path.exists(f"{save_directory}/rollcalls"):
            os.makedirs(f"{save_directory}/rollcalls")

        rollcall_file = f"{save_directory}/rollcalls/{datetime_string}-rollcall-{year}-{rollcall_id}.md"

        with open(rollcall_file, 'w') as file:
            # Get file name from file path
            file.write(f"# Roll Call {year}-{rollcall_id}\n")
            file.write(f"\nRoll Call Time: {datetime_string}\n")
            file.write(f"\nVote Question: {rollcall_data['Question']}\n")

            dated_bill_name = make_dated_filename(rollcall_data['BillDateTime'], rollcall_data['BillName'])
            file.write(f"\nBill Version: {dated_bill_name}\n")

            if amendment_filename := rollcall_data['AmendmentName']:
                amendment_filepath = make_txt_filepath(bill_folder_string, amendment_filename)
                amendment_str = open(amendment_filepath).read()
                file.write(f"\nAmendment Version: {amendment_filename}\n")
                file.write(f"\n# Amendment Summary\n{amendment_str}\n")

            if summary:
                file.write(f"\n{summary}\n")

            # Loop through each vote and write to the file as a markdown table
            # Each vote has the following format {'name': name, 'party': party, 'state': state, 'vote': vote_type}
            previous_votes = {vote['CongressmanID']: vote['Vote'] for vote in previous_rollcall_data['Votes']} if previous_rollcall_data else None
            file.write("\n# Votes\n")
            file.write("\n| Name | Party | State | Vote " + ("| Previous Vote |\n" if previous_votes else "|\n"))
            file.write("|------|-------|-------|------" + ("|---------------|\n" if previous_votes else "|\n"))
            for vote in rollcall_data['Votes']:
                if previous_votes:
                    previous_vote = previous_votes.get(vote['CongressmanID'])
                    file.write(f"| {vote['Name']} | {vote['Party']} | {vote['State']} | {vote['Vote']} | {previous_vote} |\n")
                else:
                    file.write(f"| {vote['Name']} | {vote['Party']} | {vote['State']} | {vote['Vote']} |\n")

        print(f"Saved votes for {rollcall_id} to {rollcall_file}")

    def write_hr_legislator_report(self, congressman_id, save_directory):
        """Generate a report for a congressman showing top industry donors and related bills."""
        # Get congressman details
        congressman_details = self.congress_db_.get_congressman_details(congressman_id)
        if not congressman_details:
            print(f"No congressman found with ID {congressman_id}")
            return

        last_name = congressman_details['last_name']
        state_code = congressman_details['state_code']

        # Get top industry donors
        top_donors = self.congress_db_.get_top_donors(congressman_id)

        # Get related bills
        related_bills = self.congress_db_.get_related_bills(congressman_id)

        # Create report file
        report_file = f"{save_directory}/hr_legislators/{state_code}_{last_name}_report.md"
        with open(report_file, 'w') as file:
            file.write(f"# Report for {last_name} ({state_code})\n")
            file.write("\n## Top Industry Donors\n")
            file.write("| Industry Description | Donation Amount |\n")
            file.write("|----------------------|-----------------|\n")
            for donor in top_donors:
                file.write(f"| {donor['Description']} | ${donor['DonationAmount']:,.2f} |\n")

            file.write("\n## Related Bills\n")
            file.write("| Bill Name |\n")
            file.write("|-----------|\n")
            for bill in related_bills:
                file.write(f"| {bill[0]} |\n")

        print(f"Report saved to {report_file}")
