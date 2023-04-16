import pytest
from accountability.bill_scraper import get_text_from_bill_xml_url


@pytest.fixture
def mock_requests_get(mocker):
    return mocker.patch('requests.get')


class MockResponse:
    content = ''

    def __init__(self, content):
        self.content = content


def test_When_JointResolutionURLProvided_Expect_JointResolutionTextReturned(mock_requests_get):
    url = 'https://www.govinfo.gov/content/pkg/BILLS-118hjres7pcs/xml/BILLS-118hjres7pcs.xml'

    with open('joint_resolution.xml', 'r') as file:
        bill_text = file.read()

    mock_requests_get.return_value = MockResponse(bill_text)
    text = get_text_from_bill_xml_url(url)
    assert text == 'That, pursuant to section 202 of the National Emergencies Act ( 50 U.S.C. 1622 ), the national ' \
                   'emergency declared by the finding of the President on March 13, 2020, in Proclamation 9994 (85 ' \
                   'Fed. Reg. 15337) is hereby terminated.'
    mock_requests_get.assert_called_once_with(url)

#TODO: create a test to check if legis-body and engrossed-amendment-body can be scraped