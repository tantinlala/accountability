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

    def write_top_industries_to_files(self, cycle=''):
        """
        Writes the top industry contributors for each representative to a file.

        :param cycle: Election cycle (e.g., '2022'). Defaults to the most recent cycle if blank.
        """
        output_dir = 'profiles'
        os.makedirs(output_dir, exist_ok=True)
        
        for state_abbr in self.state_abbreviations:
            legislators = self.get_legislators(state_abbr)
            if 'response' in legislators and 'legislator' in legislators['response']:
                for legislator in legislators['response']['legislator']:
                    cid = legislator['@attributes']['cid']
                    lastname = legislator['@attributes']['lastname']
                    firstlast = legislator['@attributes']['firstlast']
                    party = legislator['@attributes']['party']
                    office = legislator['@attributes']['office']
                    phone = legislator['@attributes']['phone']
                    fax = legislator['@attributes']['fax']
                    website = legislator['@attributes']['website']
                    webform = legislator['@attributes']['webform']
                    twitter_id = legislator['@attributes']['twitter_id']
                    
                    print(f"Fetching top industries for legislator {cid} in state {state_abbr} for cycle {cycle}...")
                    industries = self.get_top_industry_contributors(cid, cycle)
                    file_path = os.path.join(output_dir, f"profile_{state_abbr}_{lastname}.txt")
                    if not os.path.exists(file_path):
                        with open(file_path, 'w') as file:
                            file.write(f"Name: {firstlast}\n")
                            file.write(f"CID: {cid}\n")
                            file.write(f"Party: {party}\n")
                            file.write(f"Office: {office}\n")
                            file.write(f"Phone: {phone}\n")
                            file.write(f"Fax: {fax}\n")
                            file.write(f"Website: {website}\n")
                            file.write(f"Webform: {webform}\n")
                            file.write(f"Twitter: {twitter_id}\n")
                            file.write("Top Industry Donors:\n")
                            if industries:
                                for industry in industries['response']['industries']['industry']:
                                    industry_name = industry['@attributes']['industry_name']
                                    total = industry['@attributes']['total']
                                    file.write(f"  - {industry_name}: ${total}\n")
                        print(f"Wrote information for legislator {cid} to {file_path}")
                    else:
                        print(f"Skipping saving {file_path} because it already exists")

if __name__ == '__main__':
    secrets_parser = SecretsParser()
    secrets_parser.parse_secrets_file('secrets.yaml')
    donorship = Donorship(secrets_parser)

    # Fetch top contributing industries for all legislators and write to files
    print("Starting to fetch top contributing industries for all legislators and write to files...")
    donorship.write_top_industries_to_files()
    print("Finished fetching and writing top contributing industries for all legislators.")