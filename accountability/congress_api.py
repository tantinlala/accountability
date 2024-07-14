import datetime
from datetime import timedelta
import requests
import pandas as pd

class CongressGovAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.congress.gov/v3"
        
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
        return response.json().get('bills', [])

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