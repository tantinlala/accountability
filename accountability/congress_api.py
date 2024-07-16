import datetime
from datetime import timedelta
import requests
import pandas as pd
import os
import json

class CongressAPI:
    SECRET_GROUP = 'congress'
    SECRET_NAME = 'CONGRESS_API_KEY'
    BASE_URL = "https://api.congress.gov/v3"

    def __init__(self, secrets_parser):
        if secrets_parser is not None:
            api_key = secrets_parser.get_secret(self.SECRET_GROUP, self.SECRET_NAME)

        self.api_key = api_key
        self.bills = None

    def save_bill_as_text(self, bill_id, update_date, save_directory):
        """
        Download the text of a bill and save it to a file.
        :param bill_id: The ID of the bill to download
        :param save_directory: The directory where the bill text file will be saved.
        """
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)

        result = self.download_bill_text(update_date, bill_id)

        if result is None:
            print(f"Skipping bill {bill_id} because no text was found")
            return

        (bill_text, version_date) = result

        bill_file_name = bill_id.replace('/', '-')
        bill_file_name = f"{version_date}-{bill_file_name}"
        file_path = os.path.join(save_directory, f"{bill_file_name}.txt")

        # Only save the bill if it doesn't already exist
        if os.path.exists(file_path):
            print(f"Skipping bill {bill_id} version with timestamp {version_date} because it already exists")
            return

        with open(file_path, 'w') as file:
            file.write(bill_text)

        print(f"Saved {bill_id} to {file_path}")

    def save_bills_as_text(self, save_directory):
        """
        Goes through each bill found via get_recently_introduced_bills and stores each bill as plain text in a file.
        :param save_directory: The directory where the bill text files will be saved.
        """

        for bill in self.bills:
            bill_type = bill['type'].lower()
            bill_id = f"{bill['congress']}/{bill_type}/{bill['number']}"
            self.save_bill_as_text(bill_id, bill['updateDateIncludingText'], save_directory)
        
    def get_recently_introduced_bills(self, time_days):
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

    def download_bill_text(self, update_date, bill_id):
        response = requests.get(f"{self.BASE_URL}/bill/{bill_id}/text", params={'api_key': self.api_key})
        response.raise_for_status()
        bill_data = response.json()

        # Print bill data with four spaces of indentation
        print(json.dumps(bill_data, indent=4))
        
        text_versions = bill_data.get('textVersions', [])
        if not text_versions:
            return None
        
        # Find the most recent text version that is older than update_date (which is a string)
        update_date = datetime.datetime.strptime(update_date, "%Y-%m-%dT%H:%M:%SZ")
        versions_less_than_update_date = [version for version in text_versions if version['date'] and datetime.datetime.strptime(version['date'], "%Y-%m-%dT%H:%M:%SZ") <= update_date]

        if not versions_less_than_update_date:
            return None

        most_recent_version = max(versions_less_than_update_date, key=lambda x: datetime.datetime.strptime(x['date'], "%Y-%m-%dT%H:%M:%SZ"))
        
        # Look for the "Formatted Text" format
        formatted_text_url = next((format['url'] for format in most_recent_version['formats'] if format['type'] == "Formatted Text"), None)
        
        if not formatted_text_url:
            return None
        
        # Step 4: Download and return the content
        text_response = requests.get(formatted_text_url)
        text_response.raise_for_status()
        return (text_response.text, most_recent_version['date'])
