from accountability.request_helper import make_request
from accountability.secrets_parser import SecretsParser
import os

class Donorship:
    SECRET_GROUP = 'opensecrets'
    SECRET_NAME = 'OPEN_SECRETS_API_KEY'

    def __init__(self, secrets_parser):
        if secrets_parser is not None:
            api_key = secrets_parser.get_secret(self.SECRET_GROUP, self.SECRET_NAME)

        self.api_key = api_key
        self.base_url = 'https://www.opensecrets.org/api/'
        self.state_abbreviations = [
            'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
            'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
            'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
            'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
            'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
        ]

    def get_top_industry_contributors(self, candidate_id, cycle=''):
        """
        Fetches the top industries contributing to a specified candidate.

        :param candidate_id: The CRP CandidateID (e.g., 'N00007360').
        :param cycle: Election cycle (e.g., '2022'). Defaults to the most recent cycle if blank.
        :return: Parsed response data or None if an error occurs.
        """
        print(f"Fetching top industry contributors for candidate {candidate_id} for cycle {cycle}...")
        params = {
            'method': 'candIndustry',
            'cid': candidate_id,
            'cycle': cycle,
            'apikey': self.api_key
        }
        return make_request(self.base_url, params)

    def get_legislators(self, state_abbr):
        """
        Fetches a list of current legislators for a specified state.

        :param state_abbr: Two-character state abbreviation (e.g., 'MA' for Massachusetts).
        :return: Parsed response data or None if an error occurs.
        """
        print(f"Fetching legislators for state {state_abbr}...")
        params = {
            'method': 'getLegislators',
            'id': state_abbr,
            'apikey': self.api_key
        }
        return make_request(self.base_url, params)

    def get_all_legislators(self):
        """
        Fetches a list of current legislators for all U.S. states.

        :return: Dictionary with state abbreviations as keys and legislator data as values.
        """
        all_legislators = {}
        for state_abbr in self.state_abbreviations:
            legislators = self.get_legislators(state_abbr)
            if legislators:
                all_legislators[state_abbr] = legislators
            else:
                print(f"Failed to retrieve data for {state_abbr}.")
        return all_legislators

    def get_all_legislators_and_contributors(self, cycle=''):
        """
        Fetches the top contributing industries for each legislator across all U.S. states.

        :param cycle: Election cycle (e.g., '2022'). Defaults to the most recent cycle if blank.
        :return: Dictionary with legislator IDs as keys and their top industries as values.
        """
        all_legislators = self.get_all_legislators()
        for state, legislators in all_legislators.items():
            if 'response' in legislators and 'legislator' in legislators['response']:
                for legislator in legislators['response']['legislator']:
                    cid = legislator['@attributes']['cid']
                    print(f"Fetching top industries for legislator {cid} in state {state} for cycle {cycle}...")
                    industries = self.get_top_industry_contributors(cid, cycle)
                    if industries:
                        legislator['top_industries'] = industries
                    else:
                        print(f"Failed to retrieve industries for CID {cid}.")
        return all_legislators

    def write_top_industries_to_files(self, cycle=''):
        """
        Writes the top industry contributors for each representative to a file.

        :param cycle: Election cycle (e.g., '2022'). Defaults to the most recent cycle if blank.
        """
        all_legislators = self.get_all_legislators_and_contributors(cycle)
        output_dir = 'top_industries'
        os.makedirs(output_dir, exist_ok=True)
        
        for state, legislators in all_legislators.items():
            if 'response' in legislators and 'legislator' in legislators['response']:
                for legislator in legislators['response']['legislator']:
                    cid = legislator['@attributes']['cid']
                    lastname = legislator['@attributes']['lastname']
                    if 'top_industries' in legislator:
                        file_path = os.path.join(output_dir, f"{state}_{lastname}_top_industries.txt")
                        with open(file_path, 'w') as file:
                            file.write(str(legislator['top_industries']))
                        print(f"Wrote top industries for legislator {cid} to {file_path}")

if __name__ == '__main__':
    secrets_parser = SecretsParser()
    secrets_parser.parse_secrets_file('secrets.yaml')
    donorship = Donorship(secrets_parser)

    # Fetch top contributing industries for all legislators and write to files
    print("Starting to fetch top contributing industries for all legislators and write to files...")
    donorship.write_top_industries_to_files()
    print("Finished fetching and writing top contributing industries for all legislators.")