from congress import Congress
import datetime
import requests
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

    def get_recent_senate_bills(self, num_months, write_to_file=False):
        """
        Gets metadata and plaintext of bills that were voted upon over the past num_months
        :param num_months: Number of months over which to get bill metadata and plaintext
        :param write_to_file: Indicate whether the plain-text version of the bills should be written to a file named after its bill id
        :return: metadata as a dictionary and names of filenames to which plaintext was written
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

        # Then, go through all the votes and find each one with a bill api_uri
        print("\n")
        bill_uris = list()
        for vote in all_votes:
            try:
                api_uri = vote['bill']['api_uri']
                if (api_uri is not None) and (api_uri not in bill_uris) and (vote['question'] in self.QUESTION_TYPES):
                    bill_uris.append(api_uri)
                    print(api_uri)
            except TypeError:
                pass
            except KeyError:
                pass

        # Finally, go through each api uri, extract relevant metadata on the bill, and extract the bill's text
        # If requested, save the bill's text to a .txt file
        print("\n")
        bill_metadata = dict()
        bill_filenames = list()
        for bill_uri in bill_uris:
            headers = {'X-API-Key': self.api_key_}
            response = requests.get(bill_uri, headers=headers)

            # Check the status code to ensure the request was successful
            if response.status_code == 200:
                bill_json = response.json()
                if len(bill_json['results']) > 0:  # TODO: figure out whether there will ever be more than 1 result
                    result = bill_json['results'][0]

                    # Loop through each version in reverse chronological order until we find one with a url for xml resource
                    # TODO: filter based off of this?:
                    # https://www.senate.gov/legislative/KeytoVersionsofPrintedLegislation.htm
                    for version in result['versions']:
                        if '.xml' in version['url']:
                            bill_id = result['bill_id']
                            bill_dict = dict()
                            bill_dict['text_url'] = version['url']
                            bill_dict['source'] = result
                            bill_metadata[bill_id] = bill_dict

                            if write_to_file:
                                bill_filename = bill_id + '.txt'
                                with open(bill_filename, 'w') as file:
                                    bill_text = get_text_from_bill_xml_url(bill_dict['text_url'])
                                    file.write(bill_text)
                                    bill_filenames.append(bill_filename)

                            print(bill_metadata[bill_id]['text_url'])
                            break
            else:
                print("An error occurred:", response.status_code)

        return bill_filenames, bill_metadata
