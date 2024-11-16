import re
import requests
import xml.etree.ElementTree as ET
import datetime
import os

class HRRollCall:
    def __init__(self):
        self.BASE_URL = url = "https://clerk.house.gov/evs"
        self.congress_ = None
        self.bill_id_ = None
        self.votes_ = []
        self.datetime_string_ = None
        self.vote_question_ = None
        self.is_amendment_vote_ = False
        self.rollcall_id_ = None
        self.vote_result_ = None

    def process_rollcall(self, year, rollcall_id):
        # Construct the URL with the roll call number
        url = f"{self.BASE_URL}/{year}/roll{rollcall_id}.xml"
        return self.process_rollcall_url(url)

    def process_rollcall_url(self, url):
        # Fetch the XML data
        response = requests.get(url)
        if response.status_code == 404:
            return False

        # Parse the XML data
        xml_data = response.content
        root = ET.fromstring(xml_data)

        # Extract the bill being voted upon
        self.congress_ = root.find('.//vote-metadata/congress').text
        self.vote_question_ = root.find('.//vote-metadata/vote-question').text
        self.vote_result_ = root.find('.//vote-metadata/vote-result').text

        # Check whether the vote is for an amendment vote
        if root.find('.//vote-metadata/amendment-num') is not None:
            self.is_amendment_vote_ = True
        else:
            self.is_amendment_vote_ = False

        # Combine action_date and action_time to get a datetime
        action_date = root.find('.//vote-metadata/action-date').text
        action_time = root.find('.//vote-metadata/action-time').text
        action_date = datetime.datetime.strptime(action_date, "%d-%b-%Y").strftime("%Y-%m-%d")
        time = re.search(r'(\d+:\d+)', action_time).group(1)
        self.datetime_string_ = f"{action_date}T{time.zfill(5)}:00Z"

        # Use regex to extract the bill id from the legis_num
        legis_num = root.find('.//vote-metadata/legis-num').text
        legis_num = legis_num.strip()
        if re.match(r'^H R \d+$', legis_num):
            legis_num = legis_num.replace('H R ', 'hr/')
        elif re.match(r'^H J RES \d+$', legis_num):
            legis_num = legis_num.replace('H J RES ', 'hjres/')
        elif re.match(r'^H RES \d+$', legis_num):
            legis_num = legis_num.replace('H RES ', 'hres/');
        elif re.match(r'^S \d+$', legis_num):
            legis_num = legis_num.replace('S ', 's/');
        self.bill_id_ = legis_num

        # Iterate through the XML elements to extract the votes
        for vote in root.findall('.//recorded-vote'):
            legislator = vote.find('legislator')
            name = re.sub(r'\s*\(.*?\)\s*', '', legislator.text).strip()

            vote_string = vote.find('vote').text
            if vote_string == "No":
                vote_string = "Nay"
            elif vote_string == "Aye":
                vote_string = "Yea"

            party = legislator.get('party')
            state = legislator.get('state')
            id = legislator.get('name-id')
            self.votes_.append({'id': id, 'name': name, 'party': party, 'state': state, 'vote': vote_string})

        # Sort the lists by state
        self.votes_.sort(key=lambda x: x['state'])
        self.rollcall_id_ = int(root.find('.//vote-metadata/rollcall-num').text)

        return True

    def get_rollcall_id(self):
        return self.rollcall_id_

    def get_congress(self):
        return self.congress_

    def get_bill_id(self):
        return self.bill_id_
    
    def get_datetime(self):
        #Turn the datetime string into a datetime object
        return datetime.datetime.strptime(self.datetime_string_, "%Y-%m-%dT%H:%M:%SZ")

    def is_amendment_vote(self):
        return self.is_amendment_vote_

    def get_votes(self):
        return self.votes_

    def get_vote_question(self):
        return self.vote_question_

    def get_vote_result(self):
        return self.vote_result_  # New method to get vote result
