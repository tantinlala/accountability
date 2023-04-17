import datetime
import requests
import json
from congress import Congress
from xml.etree import ElementTree
from typing import List


def grab_text_(root: ElementTree.Element) -> str:
    """ Grab all text data in a <text> tag
    Based on: https://github.com/a5huynh/bill-analysis/blob/master/src/python/analysis/parser.py
    and https://a5huynh.github.io/posts/2017/text-analysis-of-bills/
    """
    text = []

    if root.text:
        text.append(root.text.strip())

    for child in list(root):
        text.append(grab_text_(child))

    if root.tail:
        text.append(root.tail.strip())

    return ' '.join(text)


def find_text_tags_(root: ElementTree.Element) -> List[str]:
    """ Find all <text> tag children and grab the text content
    Based on: https://github.com/a5huynh/bill-analysis/blob/master/src/python/analysis/parser.py
    and https://a5huynh.github.io/posts/2017/text-analysis-of-bills/
    Args:
        root (ElementTree.Element): Root XML tag to start search
    """
    text = []
    for child in root:
        if child.tag == 'text':
            text.append(grab_text_(child))

        if list(child):
            text.extend(find_text_tags_(list(child)))

    return text


def get_text_from_bill_xml_url(bill_xml_url) -> str:
    """ Extract a bill's text from a url containing an xml resource.
    Based on: https://github.com/a5huynh/bill-analysis/blob/master/src/python/analysis/parser.py
    and https://a5huynh.github.io/posts/2017/text-analysis-of-bills/
    Args:
        bill_xml_url (str): XML file path.
    Returns:
        str: The combined text from the bill representing the legislation
    """

    response = requests.get(bill_xml_url)
    bill_xml = ElementTree.fromstring(response.content)

    # TODO: make this cleaner
    legislation = bill_xml.find('./legis-body')
    if legislation is None:
        legislation = bill_xml.find('./resolution-body')
        if legislation is None:
            legislation = bill_xml.find('./engrossed-amendment-body')
            if legislation is None:
                return None

    return ' '.join(find_text_tags_(legislation))


class BillScraper:
    SECRET_GROUP = 'propublica'
    SECRET_NAME = 'PROPUBLICA_API_KEY'
    QUESTION_TYPES = ["On Passage of the Bill",
                      "On the Cloture Motion",
                      "On Cloture on the Motion to Proceed",
                      "On the Joint Resolution",
                      "On the Motion to Proceed",
                      "On the Motion"]

    def __init__(self, secrets_parser=None, api_key=None):
        if secrets_parser is not None:
            api_key = secrets_parser.get_secret(self.SECRET_GROUP, self.SECRET_NAME)

        if api_key is not None:
            self.congress_ = Congress(api_key)

        self.api_key_ = api_key
        self.bill_metadata = dict()

    def download_recent_senate_bills_and_votes(self, num_months):
        """
        Gets metadata of bills that were voted upon over the past num_months
        :param num_months: Number of months over which to get bill metadata
        :return: metadata as a dictionary
        """

        # First, find all congressional votes that happened within the latest num_months
        # TODO: account for num_months > 12
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

        # Then, go through all the votes and find each one with a bill api_uri and a vote_uri
        # TODO: check assumption that this is in reverse chronological order
        print("\n")
        candidate_data = list()
        bill_uris = list()
        for vote in all_votes:
            try:
                bill_uri = vote['bill']['api_uri']
                vote_uri = vote['vote_uri']
                question = vote['question']
                if (question in self.QUESTION_TYPES) and (bill_uri is not None) and (bill_uri not in bill_uris):
                    if vote_uri is not None:
                        candidate = dict()
                        candidate['bill_uri'] = bill_uri
                        candidate['vote_uri'] = vote_uri
                        candidate['question'] = question
                        candidate_data.append(candidate)

                        bill_uris.append(bill_uri)
            except TypeError:
                pass
            except KeyError:
                pass

        # Finally, go through each api uri, extract relevant metadata on the bill,
        # save off results of vote on the bill, and extract the bill's text
        # If requested, save the bill's text to a .txt file.
        print("\n")
        for candidate in candidate_data:
            headers = {'X-API-Key': self.api_key_}
            response = requests.get(candidate['bill_uri'], headers=headers)

            # Check the status code to ensure the request was successful
            if response.status_code == 200:
                bill_json = response.json()
                if len(bill_json['results']) > 0:
                    # TODO: figure out whether there will ever be more than 1 result
                    result = bill_json['results'][0]

                    # Loop through each version in reverse chronological order until we find one with a url for xml resource
                    # TODO: double check to make sure this is listed in reverse chronological order
                    # TODO: filter based off of this?:
                    # https://www.senate.gov/legislative/KeytoVersionsofPrintedLegislation.htm
                    for version in result['versions']:
                        if '.xml' in version['url']:
                            # Now try getting vote date
                            headers = {'X-API-Key': self.api_key_}
                            response = requests.get(candidate['vote_uri'], headers=headers)

                            if response.status_code == 200:
                                vote_json = response.json()

                                # Now we have all the information we need to build upon the metadata ditionary
                                bill_id = result['bill_id']
                                bill_dict = dict()
                                bill_dict['text_url'] = version['url']
                                bill_dict['bill_uri'] = candidate['bill_uri']
                                bill_dict['vote_uri'] = candidate['vote_uri']
                                bill_dict['question'] = candidate['question']
                                bill_dict['positions'] = vote_json['results']['votes']['vote']['positions']
                                self.bill_metadata[bill_id] = bill_dict
                                break  # We got a valid version, no need to loop through subsequent versions
                            else:
                                print("An error occurred when getting vote data: ", response.status_code)
            else:
                print("An error occurred when getting bill data: ", response.status_code)

        return self.bill_metadata

    def write_senate_bills_to_file(self):
        """
        Downloads bill in text form and writes them to files
        :return: list of names of files that were written
        """
        bill_filenames = list()
        for bill_id in self.bill_metadata.keys():
            bill_filename = bill_id + '.txt'
            with open(bill_filename, 'w') as file:
                bill_text = get_text_from_bill_xml_url(self.bill_metadata[bill_id]['text_url'])
                file.write(bill_text)
                bill_filenames.append(bill_filename)

        return bill_filenames

    def write_metadata_to_file(self):
        """
        Writes metadata for a bill to a file
        :return: list of names of files that were written
        """
        metadata_filenames = list()
        for bill_id in self.bill_metadata.keys():
            vote_filename = 'data-' + bill_id + '.json'
            json_object = json.dumps(self.bill_metadata[bill_id], indent=4)
            with open(vote_filename, 'w') as file:
                file.write(json_object)

        return metadata_filenames

