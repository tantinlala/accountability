import os
from accountability.file_utils import make_summary_filepath, make_txt_filepath, get_diff, save_txt_if_not_exists, file_exists, make_dated_filename
from datetime import datetime

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

        bill_title = rollcall_data['BillTitle']
        vote_result = rollcall_data['VoteResult']
        url = rollcall_data['Url']

        # Create {save_directory}/rollcalls directory if it doesn't exist
        if not os.path.exists(f"{save_directory}/rollcalls"):
            os.makedirs(f"{save_directory}/rollcalls")

        rollcall_file = f"{save_directory}/rollcalls/rollcall-{year}-{rollcall_id}.md"

        with open(rollcall_file, 'w') as file:
            # Get file name from file path
            file.write(f"# Roll Call {year}-{rollcall_id}\n")
            file.write(f"\nSource: {url}\n")
            file.write(f"\nVote Question: {rollcall_data['Question']}\n")
            file.write(f"\nVote Result: {vote_result}\n")  # New line to write vote result

            # Provide table showing changes in votes
            previous_votes = {vote['LegislatorID']: vote['Vote'] for vote in previous_rollcall_data['Votes']} if previous_rollcall_data else None

            if previous_votes:
                found_change = False
                for vote in rollcall_data['Votes']:
                    present_vote = vote['Vote']
                    previous_vote = previous_votes.get(vote['LegislatorID'])
                    if previous_vote != present_vote:
                        if not found_change:
                            file.write("\n# Changes in Votes\n")
                            file.write("\n| Name | Party | State | Vote | Previous Vote |\n")
                            file.write("|------|-------|-------|------|------|\n")
                            found_change = True
                        file.write(f"| {vote['Name']} | {vote['Party']} | {vote['State']} | {present_vote} | {previous_vote} |\n")

            dated_bill_name = make_dated_filename(rollcall_data['BillDateTime'], rollcall_data['BillName'])
            bill_name_without_suffix = rollcall_data['BillName'].replace('-bill', '')
            bill_folder = "../bills/" + bill_name_without_suffix
            file.write(f"\n# Bill Title:\n{bill_title}\n")
            file.write(f"\n# Bill Version:\n[{dated_bill_name}]({bill_folder})\n")
            file.write("\n# Questions?\n")
            file.write(f"\nGo to https://chatgpt.com/g/g-UN9NGOG2T-chat-with-us-legislation and ask ChatGPT about bill {bill_name_without_suffix}\n")

            if amendment_filename := rollcall_data['AmendmentName']:
                amendment_filepath = make_txt_filepath(bill_folder_string, amendment_filename)
                amendment_str = open(amendment_filepath).read()
                amendment_summary_link = os.path.relpath(amendment_filepath, save_directory)
                file.write(f"\n# Amendment Version: [{amendment_filename}](../{amendment_summary_link})\n")
                file.write(f"\n# Amendment Summary\n{amendment_str}\n")

            if summary:
                file.write(f"\n{summary}\n")

        print(f"Saved votes for {rollcall_id} to {rollcall_file}")

    def write_hr_legislator_report(self, legislator_id, save_directory):
        """Generate a report for a legislator showing top industry donors and related bills."""
        # Get legislator details
        legislator_details = self.congress_db_.get_legislator_details(legislator_id)
        if not legislator_details:
            print(f"No legislator found with ID {legislator_id}")
            return

        last_name = legislator_details['last_name']
        state_code = legislator_details['state_code']

        # Get top industry donors
        top_donors = self.congress_db_.get_top_donors(legislator_id)

        # Get related roll call votes
        related_votes = self.congress_db_.get_related_rollcall_votes(legislator_id)

        # Create {save_directory}/hr_legislators directory if it doesn't exist
        if not os.path.exists(f"{save_directory}/hr_legislators"):
            os.makedirs(f"{save_directory}/hr_legislators")

        # Create report file
        report_file = f"{save_directory}/hr_legislators/{state_code}-{last_name}.md"
        with open(report_file, 'w') as file:
            file.write(f"# Report for Representative {last_name} ({state_code})\n")
            file.write("\n## Top Industry Donors\n")
            file.write("| Industry Description | Donation Amount |\n")
            file.write("|----------------------|-----------------|\n")
            for donor in top_donors:
                file.write(f"| {donor['Description']} | ${donor['DonationAmount']:,.2f} |\n")

            file.write("\n## Roll Call Votes Related To Top Industry Donors\n")
            file.write("| Bill Title | Vote | Related Industries | Bill ID | Roll Call | Question |\n")
            file.write("|------------|------|--------------------|---------|-----------|----------|\n")
            for vote in related_votes:
                valid_questions = [
                    "On Agreeing to the Resolution",
                    "On Motion to Suspend the Rules and Pass",
                    "On Passage",
                    "On Motion to Suspend the Rules and Pass, as Amended",
                    "On Agreeing to the Amendment",
                    "On Motion to Suspend the Rules and Concur in the Senate Amendment"
                ]
                if vote['Question'] not in valid_questions:
                    continue
                bill_datetime_obj = datetime.strptime(vote['BillDateTime'], '%Y-%m-%d %H:%M:%S')
                bill_id = f"{bill_datetime_obj.strftime('%Y-%m-%dT%H:%M:%SZ')}-{vote['BillName']}"
                bill_name_without_suffix = vote['BillName'].replace('-bill', '')
                bill_folder = "../bills/" + bill_name_without_suffix
                bill_title = vote['BillTitle']
                roll_call = f"{vote['Year']}-{vote['RollCallID']}"
                roll_call_link = f"../rollcalls/{vote['ActionDateTime']}-rollcall-{vote['Year']}-{vote['RollCallID']}.md"
                file.write(f"| {bill_title} | {vote['Vote']} | {', '.join(vote['RelatedIndustries'])} | [{bill_id}]({bill_folder}) | [{roll_call}]({roll_call_link}) | {vote['Question']} |\n")

        print(f"Report saved to {report_file}")
