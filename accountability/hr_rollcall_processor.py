import re
import requests
import xml.etree.ElementTree as ET
import datetime
import os

class HRRollCallProcessor:
    def __init__(self):
        self.BASE_URL = url = "https://clerk.house.gov/evs"
        self.congress_ = None
        self.bill_id_ = None
        self.votes_ = []
        self.action_datetime_ = None
        self.vote_question_ = None
        self.is_amendment_vote_ = False
        self.rollcall_number_ = None

    def process_rollcall(self, year, rollcall_number):
        self.bill_id_ = None
        self.votes_ = []
        self.action_datetime_ = None

        # Construct the URL with the roll call number
        url = f"{self.BASE_URL}/{year}/roll{rollcall_number}.xml"

        # Fetch the XML data
        response = requests.get(url)
        if response.status_code == 404:
            return

        xml_data = response.content

        # Parse the XML data
        root = ET.fromstring(xml_data)

        # Extract the bill being voted upon
        legis_num_ = root.find('.//vote-metadata/legis-num').text
        congress = root.find('.//vote-metadata/congress').text
        action_date = root.find('.//vote-metadata/action-date').text
        action_time = root.find('.//vote-metadata/action-time').text
        self.vote_question_ = root.find('.//vote-metadata/vote-question').text
        if root.find('.//vote-metadata/amendment-num') is not None:
            self.is_amendment_vote_ = True
        else:
            self.is_amendment_vote_ = False

        # Convert action_date to desired format
        action_date = datetime.datetime.strptime(action_date, "%d-%b-%Y").strftime("%Y-%m-%d")

        # Extract the time from action_time
        time = re.search(r'(\d+:\d+)', action_time).group(1)

        # Combine action_date and time to get the desired format
        self.action_datetime_ = f"{action_date}T{time.zfill(5)}:00Z"

        # Use regex to check whether legis_num_ matches the format H R 1234
        legis_num_ = legis_num_.strip()
        if re.match(r'^H R \d+$', legis_num_):
            legis_num_ = legis_num_.replace('H R ', 'hr/')
        elif re.match(r'^H J RES \d+$', legis_num_):
            legis_num_ = legis_num_.replace('H J RES ', 'hjres/')
        elif re.match(r'^H RES \d+$', legis_num_):
            legis_num_ = legis_num_.replace('H RES ', 'hres/');
        elif re.match(r'^S \d+$', legis_num_):
            legis_num_ = legis_num_.replace('S ', 's/');

        self.congress_ = congress
        self.bill_id_ = legis_num_

        # Iterate through the XML elements to extract the votes
        for vote in root.findall('.//recorded-vote'):
            legislator = vote.find('legislator')
            name = legislator.text
            vote_type = vote.find('vote').text
            party = legislator.get('party')
            state = legislator.get('state')
            self.votes_.append({'name': name, 'party': party, 'state': state, 'vote': vote_type})

        # Sort the lists by state
        self.votes_.sort(key=lambda x: x['state'])
        self.rollcall_number_ = rollcall_number

    def get_congress(self):
        return self.congress_

    def get_bill_id(self):
        return self.bill_id_
    
    def get_action_datetime(self):
        return self.action_datetime_

    def is_amendment_vote(self):
        return self.is_amendment_vote_

    def save_rollcall_as_md(self, save_directory, bill_file_path, amendment_file_path=None):
        # Save information on the rollcall to an .md file

        # Create file path for roll call
        rollcall_file = f"{save_directory}/{self.action_datetime_}-rollcall-{self.rollcall_number_}.md"

        with open(rollcall_file, 'w') as file:
            # Get file name from file path
            file_name = os.path.basename(bill_file_path)
            file.write(f"Bill Version File: {file_name}\n\n")
            file.write(f"Roll Call Time: {self.action_datetime_}\n\n")
            file.write(f"Vote Question: {self.vote_question_}\n\n")
            if amendment_file_path is not None:
                file.write(f"Amendment File: {os.path.basename(amendment_file_path)}\n\n")

            # Loop through each vote and write to the file as a markdown table
            # Each vote has the following format {'name': name, 'party': party, 'state': state, 'vote': vote_type}
            file.write("| Name | Party | State | Vote |\n")
            file.write("|------|-------|-------|------|\n")
            for vote in self.votes_:
                decision = vote['vote']
                if decision == "No":
                    decision = "Nay"
                elif decision == "Aye":
                    decision = "Yea"

                file.write(f"| {vote['name']} | {vote['party']} | {vote['state']} | {decision} |\n")

        print(f"Saved votes for {self.rollcall_number_} to {rollcall_file}")
