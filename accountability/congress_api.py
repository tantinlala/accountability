import datetime
from datetime import timedelta
import requests
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

    def _convert_to_datetime(self, action_datetime_string):
        try:
            return datetime.datetime.strptime(action_datetime_string, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            return datetime.datetime.strptime(action_datetime_string, "%Y-%m-%d %H:%M:%S")

    def _download_text(self, endpoint, action_datetime):
        # Find the most recent text version that is older than action date time (which is a string)
        print(f"Downloading {endpoint} associated with action at {action_datetime}")

        response = requests.get(endpoint, params={'api_key': self.api_key})
        response.raise_for_status()
        text_versions_data = response.json()

        text_versions = text_versions_data.get('textVersions', [])
        if not text_versions:
            print(f"No text versions found for {endpoint}")
            return None
        
        versions_less_than_action_datetime = [version for version in text_versions if version['date'] and datetime.datetime.strptime(version['date'], "%Y-%m-%dT%H:%M:%SZ") <= action_datetime]

        if not versions_less_than_action_datetime:
            # Return the most recent version if there are no versions older than update_date
            print("No text versions older than action date time found")
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

    def download_bill_text(self, congress, bill_id, action_datetime_string):
        """
        Download the text of a bill and save it to a file.
        :param congress: The congress number of the bill
        :param bill_id: The ID of the bill to download
        :param action_datetime: The datetime of the bill action
        :param save_directory: The directory where the bill text file will be saved.
        """

        endpoint = f"{self.BASE_URL}/bill/{congress}/{bill_id}/text"
        action_datetime = self._convert_to_datetime(action_datetime_string)
        result = self._download_text(endpoint, action_datetime)

        if result is None:
            return None

        (bill_text, version_date) = result

        bill_name = f"{congress}-{bill_id.replace('/', '-')}-bill"
        return (bill_name, version_date, bill_text)
        
    def download_amendment_text(self, congress, bill_id, action_datetime_string):
        response = requests.get(f"{self.BASE_URL}/bill/{congress}/{bill_id}/amendments", params={'api_key': self.api_key})
        response.raise_for_status()
        amendment_data = response.json()
        amendments = amendment_data.get('amendments', [])

        if not amendments:
            print(f"No amendments found for {congress}/{bill_id}")
            return None

        # Find the most recent amendment that is older than action date time (which is a string)
        action_datetime = self._convert_to_datetime(action_datetime_string)

        amendments_older_than_action_datetime = [x for x in amendments if datetime.datetime.strptime(x['latestAction']['actionDate'] + x['latestAction']['actionTime'], "%Y-%m-%d%H:%M:%S") <= (action_datetime + timedelta(minutes=5))]

        if not amendments_older_than_action_datetime:
            # Return the most recent version if there are no versions older than update_date
            closest_amendment = max(amendments, key=lambda x: datetime.datetime.strptime(x['latestAction']['actionDate'] + x['latestAction']['actionTime'], "%Y-%m-%d%H:%M:%S"))
        else:
            closest_amendment = max(amendments_older_than_action_datetime, key=lambda x: datetime.datetime.strptime(x['latestAction']['actionDate'] + x['latestAction']['actionTime'], "%Y-%m-%d%H:%M:%S"))

        amendment_type = closest_amendment['type'].lower()
        amendment_num = closest_amendment['number']
        endpoint = f"{self.BASE_URL}/amendment/{congress}/{amendment_type}/{amendment_num}/text"
        result = self._download_text(endpoint, action_datetime)

        if result is None: 
            amendment_text = closest_amendment['description']
            version_date = closest_amendment['updateDate']
        else:
            (amendment_text, version_date) = result

        amendment_name = f"{congress}-{bill_id.replace('/', '-')}-{amendment_type}-{amendment_num}"
        return (amendment_name, version_date, amendment_text)

    def get_older_rollcalls_for_bill(self, congress, bill_id, present_rollcall):
        response = requests.get(f"{self.BASE_URL}/bill/{congress}/{bill_id}/actions", params={'api_key': self.api_key})
        response.raise_for_status()
        # Pretty print json
        print(json.dumps(response.json(), indent=4))

        rollcalls = []

        for action in response.json()['actions']:
            # Check whether "recordedVotes" key is in the action dictionary
            if 'recordedVotes' in action:
                for recorded_vote in action['recordedVotes']:
                    # Add url to rollcalls if not already in rollcall list
                    if recorded_vote['chamber'] == 'House' and recorded_vote['url'] not in rollcalls:
                        rollcalls.append(recorded_vote['url'])

        print(rollcalls)