import datetime
from datetime import timedelta
import requests
import pandas as pd
import os

class CongressAPI:
    SECRET_GROUP = 'congress'
    SECRET_NAME = 'CONGRESS_API_KEY'
    BASE_URL = "https://api.congress.gov/v3"

    def __init__(self, secrets_parser):
        if secrets_parser is not None:
            api_key = secrets_parser.get_secret(self.SECRET_GROUP, self.SECRET_NAME)

        self.api_key = api_key
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

            if bill_text is None:
                print(f"Skipping bill {bill_id} because no text was found")
                continue

            bill_file_name = f"{bill['updateDateIncludingText']}-{bill['congress']}-{bill_type}-{bill['number']}"
            file_path = os.path.join(save_directory, f"{bill_file_name}.txt")
            with open(file_path, 'w') as file:
                file.write(bill_text)
            print(f"Saved {bill_id} to {file_path}")
        
    def get_recent_bills(self, time_days):
        end_date = datetime.datetime.now()
        start_date = end_date - timedelta(days=time_days)
        params = {
            'api_key': self.api_key,
            'fromDateTime': start_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'toDateTime': end_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'limit': 250
        }
        response = requests.get(f"{self.BASE_URL}/bill", params=params)
        response.raise_for_status()
        self.bills = response.json().get('bills', [])
        return self.bills

    def download_bill_text(self, bill_id):
        response = requests.get(f"{self.BASE_URL}/bill/{bill_id}/text", params={'api_key': self.api_key})
        response.raise_for_status()
        bill_data = response.json()
        
        # Step 1 & 2: Find the most recent text version
        text_versions = bill_data.get('textVersions', [])
        if not text_versions:
            return None
        
        most_recent_version = max(text_versions, key=lambda x: datetime.datetime.strptime(x['date'], "%Y-%m-%dT%H:%M:%SZ") if x['date'] else datetime.datetime.min)
        
        # Step 3: Look for the "Formatted Text" format
        formatted_text_url = next((format['url'] for format in most_recent_version['formats'] if format['type'] == "Formatted Text"), None)
        
        if not formatted_text_url:
            return None
        
        # Step 4: Download and return the content
        text_response = requests.get(formatted_text_url)
        text_response.raise_for_status()
        return text_response.text
