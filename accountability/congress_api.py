import datetime
from datetime import timedelta
import json
import requests
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

    def _save_if_not_exists(self, save_directory, file_name, content):
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)

        file_path = os.path.join(save_directory, f"{file_name}.txt")

        if not os.path.exists(file_path):
            with open(file_path, 'w') as file:
                file.write(content)
            print(f"Saved to {file_path}")
        else:
            print(f"Skipping saving {file_path} because it already exists")

        return file_path

    def _download_text(self, endpoint, action_datetime):
        print(f"Downloading {endpoint} text at {action_datetime}")
        response = requests.get(endpoint, params={'api_key': self.api_key})
        response.raise_for_status()
        text_versions_data = response.json()

        text_versions = text_versions_data.get('textVersions', [])
        if not text_versions:
            print(f"No text versions found for {endpoint}")
            return None
        
        # Find the most recent text version that is older than action date time (which is a string)
        try:
            action_datetime = datetime.datetime.strptime(action_datetime, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            action_datetime = datetime.datetime.strptime(action_datetime, "%Y-%m-%d")

        versions_less_than_action_datetime = [version for version in text_versions if version['date'] and datetime.datetime.strptime(version['date'], "%Y-%m-%dT%H:%M:%SZ") <= action_datetime]

        if not versions_less_than_action_datetime:
            # Return the most recent version if there are no versions older than update_date
            most_recent_version = max(text_versions, key=lambda x: datetime.datetime.strptime(x['date'], "%Y-%m-%dT%H:%M:%SZ"))
        else:
            most_recent_version = max(versions_less_than_action_datetime, key=lambda x: datetime.datetime.strptime(x['date'], "%Y-%m-%dT%H:%M:%SZ"))
        
        # Look for the "Formatted Text" format
        formatted_text_url = next((format['url'] for format in most_recent_version['formats'] if format['type'] == "Formatted Text"), None)
        
        if not formatted_text_url:
            # Try looking for "Formatted XML"
            formatted_text_url = next((format['url'] for format in most_recent_version['formats'] if format['type'] == "Formatted XML"), None)
            if not formatted_text_url:
                print(f"No formatted text or XML found for {endpoint}")
                return None
        
        # Download and return the content
        text_response = requests.get(formatted_text_url)
        text_response.raise_for_status()
        return (text_response.text, most_recent_version['date'])

    def save_bills_as_text(self, time_days, save_directory):
        """
        Goes through each bill within the last specified number of days and stores each bill as plain text in a file.
        :param time_days: The number of days to go back to get bills.
        :param save_directory: The directory where the bill text files will be saved.
        """
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
        bills = response.json().get('bills', [])

        for bill in bills:
            bill_type = bill['type'].lower()
            bill_id = f"{bill_type}/{bill['number']}"
            self.save_bill_as_text(bill['congress'], bill_id, bill['updateDateIncludingText'], save_directory)

    def save_bill_as_text(self, congress, bill_id, action_datetime, save_directory):
        """
        Download the text of a bill and save it to a file.
        :param congress: The congress number of the bill
        :param bill_id: The ID of the bill to download
        :param action_datetime: The datetime of the bill action
        :param save_directory: The directory where the bill text file will be saved.
        """

        endpoint = f"{self.BASE_URL}/bill/{congress}/{bill_id}/text"
        result = self._download_text(endpoint, action_datetime)

        if result is None:
            return None

        (bill_text, version_date) = result

        file_name = f"{version_date}-{congress}-{bill_id.replace('/', '-')}"
        file_path = self._save_if_not_exists(save_directory, file_name, bill_text)
        return (version_date, file_path)
        
    def save_amendment_as_text(self, congress, bill_id, action_datetime, save_directory):
        response = requests.get(f"{self.BASE_URL}/bill/{congress}/{bill_id}/amendments", params={'api_key': self.api_key})
        response.raise_for_status()
        amendment_data = response.json()
        amendments = amendment_data.get('amendments', [])

        if not amendments:
            print(f"No amendments found for {congress}/{bill_id}")
            return None

        # Find the amendment whose actionDate and actionTime are closest to the action_datetime
        action_datetime = datetime.datetime.strptime(action_datetime, "%Y-%m-%dT%H:%M:%SZ")
        closest_amendment = min(amendments, key=lambda x: abs(datetime.datetime.strptime(x['latestAction']['actionDate'] + x['latestAction']['actionTime'], "%Y-%m-%d%H:%M:%S") - action_datetime))

        amendment_type = closest_amendment['type'].lower()
        amendment_num = closest_amendment['number']
        endpoint = f"{self.BASE_URL}/amendment/{congress}/{amendment_type}/{amendment_num}/text"
        result = self._download_text(endpoint, action_datetime)

        if result is None: 
            amendment_text = closest_amendment['description']
            version_date = closest_amendment['updateDate']
        else:
            (amendment_text, version_date) = result

        file_name = f"{version_date}-{congress}-{bill_id.replace('/', '-')}-{amendment_type}-{amendment_num}"
        file_path = self._save_if_not_exists(save_directory, file_name, amendment_text)
        return (version_date, file_path)
