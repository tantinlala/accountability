import re
import requests
import xml.etree.ElementTree as ET
import datetime

class RollCallProcessor:
    def __init__(self):
        self.BASE_URL = url = "https://clerk.house.gov/evs/2024/roll"
        self.bill_id_ = None
        self.yay_votes_ = []
        self.nay_votes_ = []
        self.action_datetime_ = None

    def process_roll_call(self, roll_call_number):
        # Construct the URL with the roll call number
        url = f"{self.BASE_URL}{roll_call_number}.xml"

        # Fetch the XML data
        response = requests.get(url)
        if response.status_code == 404:
            self.bill_id_ = None
            self.yay_votes_ = []
            self.nay_votes_ = []
            self.action_datetime_ = None
            return

        xml_data = response.content

        # Parse the XML data
        root = ET.fromstring(xml_data)

        # Extract the bill being voted upon
        legis_num_ = root.find('.//vote-metadata/legis-num').text
        congress_ = root.find('.//vote-metadata/congress').text
        action_date = root.find('.//vote-metadata/action-date').text
        action_time = root.find('.//vote-metadata/action-time').text

        # Convert action_date to desired format
        action_date = datetime.datetime.strptime(action_date, "%d-%b-%Y").strftime("%Y-%m-%d")

        # Extract the time from action_time
        time = re.search(r'(\d+:\d+)', action_time).group(1)

        # Combine action_date and time to get the desired format
        self.action_datetime_ = f"{action_date}T{time}:00Z"

        # Use regex to check whether legis_num_ matches the format H R 1234
        legis_num_ = legis_num_.strip()
        if re.match(r'^H R \d+$', legis_num_):
            legis_num_ = legis_num_.replace('H R ', 'hr/')
        elif re.match(r'^H J RES \d+$', legis_num_):
            legis_num_ = legis_num_.replace('H J RES ', 'hjres/')
        elif re.match(r'^H RES \d+$', legis_num_):
            legis_num_ = legis_num_.replace('H RES ', 'hres/');

        self.bill_id_ = f"{congress_}/{legis_num_}"

        # Iterate through the XML elements to extract the votes
        for vote in root.findall('.//recorded-vote'):
            legislator = vote.find('legislator')
            name = legislator.text
            vote_type = vote.find('vote').text
            party = legislator.get('party')
            state = legislator.get('state')
            
            if vote_type == 'Yea':
                self.yay_votes_.append({'name': name, 'party': party, 'state': state})
            elif vote_type == 'Nay':
                self.nay_votes_.append({'name': name, 'party': party, 'state': state})

        # Sort the lists by state
        self.yay_votes_.sort(key=lambda x: x['state'])
        self.nay_votes_.sort(key=lambda x: x['state'])

    def get_bill_id(self):
        return self.bill_id_
    
    def get_yay_votes(self):
        return self.yay_votes_
    
    def get_nay_votes(self):
        return self.nay_votes_

    def get_action_datetime(self):
        return self.action_datetime_

# Example usage
if __name__ == "__main__":
    processor = RollCallProcessor()
    roll_call_number = 353  # Example roll call number
    processor.process_roll_call(roll_call_number)