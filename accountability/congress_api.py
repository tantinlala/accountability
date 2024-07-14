import datetime
from datetime import timedelta
import requests
import pandas as pd
import os

class CongressGovAPI:
    def __init__(self, api_key):
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
            bill_id = f"{bill['congress']}/{bill['type']}/{bill['number']}"
            try:
                bill_text = self.download_bill_text(bill_id)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    print(f"Bill {bill_id} not found. Skipping...")
                    continue
                else:
                    raise e
            bill_text = self.download_bill_text(bill_id)
            file_path = os.path.join(save_directory, f"{bill_id}.txt")
            with open(file_path, 'w') as file:
                file.write(bill_text)
            print(f"Saved {bill_id} to {file_path}")
        
    def get_recent_bills(self, months_back=1):
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
        return response.text

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