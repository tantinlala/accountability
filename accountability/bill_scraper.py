#TODO: get ProPublica api key

#TODO: download all bills up to 3 months that isn't presently in database

#TODO: download text of all unique bills
# - replace using congress api with ProPublica api
# https://projects.propublica.org/api-docs/congress-api/
# go through unique bills that are left in the list and download xml (base this on latest date before vote date of version)
# https://www.senate.gov/legislative/KeytoVersionsofPrintedLegislation.htm

from congress import Congress
import datetime
import requests


class BillScraper:
    SECRET_GROUP = 'propublica'
    SECRET_NAME = 'PROPUBLICA_API_KEY'
    QUESTION_TYPES = ["On Passage of the Bill",
                      "On the Cloture Motion",
                      "On Cloture on the Motion to Proceed",
                      "On the Joint Resolution",
                      "On the Motion to Proceed",
                      "On the Motion"]

    def __init__(self, secrets_parser):
        self.api_key_ = secrets_parser.get_secret(self.SECRET_GROUP, self.SECRET_NAME)
        self.congress_ = Congress(self.api_key_)

    def get_recent_senate_bills(self, num_months):
        current_year = datetime.date.today().year
        current_month = datetime.date.today().month

        all_votes = []
        for i in range(num_months):
            month = current_month - i
            year = current_year
            if month <= 0:
                month += 12
                year = current_year - 1

            months_votes = self.congress_.votes.by_month('senate', year=year, month=month)
            all_votes += months_votes['votes']

        bills = dict()
        for vote in all_votes:
            try:
                api_uri = vote['bill']['api_uri']
                bill_id = vote['bill']['bill_id']
                if api_uri not in bills and vote['question'] in self.QUESTION_TYPES:
                    bills[bill_id] = dict()
                    bills[bill_id]['api_uri'] = api_uri
            except TypeError:
                pass
            except KeyError:
                pass

        for bill_id in bills.keys():
            headers = {'X-API-Key': self.api_key_}
            response = requests.get(bills[bill_id]['api_uri'], headers=headers)

            # Check the status code to ensure the request was successful
            try:
                if response.status_code == 200:
                    bill_json = response.json()
                    bills[bill_id]['text'] = bill_json['results'][0]['versions'][0]['url']
                else:
                    print("An error occurred:", response.status_code)
            except IndexError:
                bills[bill_id]['text'] = ''

            print(bills[bill_id]['text'])


