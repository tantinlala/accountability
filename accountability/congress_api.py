import datetime
from datetime import timedelta
import requests
import pandas as pd
import os

class CongressAPI:
    SECRET_GROUP = 'congress'
    SECRET_NAME = 'CONGRESS_API_KEY'

    def __init__(self, secrets_parser):
        if secrets_parser is not None:
            api_key = secrets_parser.get_secret(self.SECRET_GROUP, self.SECRET_NAME)

        self.api_key = api_key
        self.base_url = "https://api.congress.gov/v3"
        self.bills = None

    def save_bills_as_text(self, save_directory):
        """
        Goes through each bill found via get_recent_bills and stores each bill as plain text in a file.
        :param save_directory: The directory where the bill text files will be saved.
        """
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)

        for bill in self.bills:
            bill_type = bill['type'].lower()
            bill_id = f"{bill['congress']}/{bill_type}/{bill['number']}"
            bill_text = self.download_bill_text(bill_id)

            bill_file_name = f"{bill['congress']}-{bill_type}-{bill['number']}"
            file_path = os.path.join(save_directory, f"{bill_file_name}.txt")
            with open(file_path, 'w') as file:
                file.write(bill_text)
            print(f"Saved {bill_id} to {file_path}")
        
    def get_recent_bills(self, months_back):
        end_date = datetime.datetime.today()
        start_date = end_date - timedelta(days=months_back*30)
        params = {
            'api_key': self.api_key,
            'fromDate': start_date.strftime('%Y-%m-%d'),
            'toDate': end_date.strftime('%Y-%m-%d'),
            'billStatus': 'Introduced'
        }
        response = requests.get(f"{self.base_url}/bill", params=params)
        response.raise_for_status()
        self.bills = response.json().get('bills', [])
        return self.bills

    def download_bill_text(self, bill_id):
        response = requests.get(f"{self.base_url}/bill/{bill_id}/text", params={'api_key': self.api_key})
        response.raise_for_status()
        bill_data = response.json()
        
        # Step 1 & 2: Find the most recent text version
        text_versions = bill_data.get('textVersions', [])
        if not text_versions:
            return "No text versions available"
        
        most_recent_version = max(text_versions, key=lambda x: datetime.datetime.strptime(x['date'], "%Y-%m-%dT%H:%M:%SZ"))
        
        # Step 3: Look for the "Formatted Text" format
        formatted_text_url = next((format['url'] for format in most_recent_version['formats'] if format['type'] == "Formatted Text"), None)
        
        if not formatted_text_url:
            return "Formatted Text version not available"
        
        # Step 4: Download and return the content
        text_response = requests.get(formatted_text_url)
        text_response.raise_for_status()
        return text_response.text

    def get_bill_votes(self, bill_id):
        response = requests.get(f"{self.base_url}/bill/{bill_id}/votes", params={'api_key': self.api_key})
        response.raise_for_status()
        return response.json().get('votes', [])

    def tabulate_votes(self, bill_id):
        votes = self.get_bill_votes(bill_id)
        vote_data = []
        for vote in votes:
            roll_call_id = vote.get('rollCallId')
            vote_position = vote.get('position')
            for member_vote in vote.get('members', []):
                vote_data.append({
                    'member_id': member_vote.get('id'),
                    'name': member_vote.get('name'),
                    'state': member_vote.get('state'),
                    'party': member_vote.get('party'),
                    'position': member_vote.get('vote')
                })
        return pd.DataFrame(vote_data)