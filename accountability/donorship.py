from accountability.request_helper import make_request
from accountability.secrets_parser import SecretsParser
import os
import pandas as pd
import json

class Donorship:
    SECRET_GROUP = 'opensecrets'
    SECRET_NAME = 'OPEN_SECRETS_API_KEY'

    def __init__(self, secrets_parser, csv_file_path='Candidate Ids - 2024-Table 1.csv'):
        if secrets_parser is not None:
            api_key = secrets_parser.get_secret(self.SECRET_GROUP, self.SECRET_NAME)

        self.api_key = api_key
        self.base_url = 'https://www.opensecrets.org/api/'

        self.df = pd.read_csv(csv_file_path, skiprows=13)
        self.df = self.df[['CID', 'CRPName', 'DistIDRunFor']]

    def get_top_donors(self, last_name, state_code, cycle=''):
        """
        Fetches the top industries contributing to a specified candidate.

        :param last_name: The last name of the candidate (e.g., 'Aadland').
        :param state_code: The state code where the candidate is running (e.g., 'CO').
        :param cycle: Election cycle (e.g., '2022'). Defaults to the most recent cycle if blank.
        :return: Parsed response data or None if an error occurs.
        """

        # Filter by CRPName where the last name matches exactly before the comma
        filtered_df = self.df[self.df['CRPName'].str.contains(last_name, case=False, na=False)]
        
        # Further filter by DistIDRunFor containing the state code (only match part without numbers)
        filtered_df = filtered_df[filtered_df['DistIDRunFor'].str.extract(r'([A-Za-z]+)', expand=False).str.contains(state_code, case=False, na=False)]
        
        # Extract the CIDs from the filtered DataFrame
        candidate_id = ''
        if not filtered_df.empty:
            candidate_id = filtered_df['CID'].tolist()[0]

        print(f"Found candidate ID {candidate_id} for {last_name} in {state_code}")

        params = {
            'method': 'candIndustry',
            'cid': candidate_id,
            'cycle': cycle,
            'apikey': self.api_key
        }
        return make_request(self.base_url, params)

if __name__ == '__main__':
    secrets_parser = SecretsParser()
    secrets_parser.parse_secrets_file('secrets.yaml')
    donorship = Donorship(secrets_parser)

    # Fetch top contributing industries for all legislators and write to files
    print("Starting to fetch top contributing industries for all legislators and write to files...")
    info = donorship.get_top_donors('britt', 'al')
    print(json.dumps(info, indent=4))

    print("Finished fetching and writing top contributing industries for all legislators.")