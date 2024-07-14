import requests
import xml.etree.ElementTree as ET

# URL of the XML file
url = "https://clerk.house.gov/evs/2024/roll355.xml"

# Fetch the XML data
response = requests.get(url)
xml_data = response.content

# Parse the XML data
root = ET.fromstring(xml_data)

# Extract the bill being voted upon
bill = root.find('.//vote-metadata/legis-num').text

# Initialize lists to store the names, party affiliations, and states of those who voted "yay" and "nay"
yay_votes = []
nay_votes = []

# Iterate through the XML elements to extract the votes
for vote in root.findall('.//recorded-vote'):
    legislator = vote.find('legislator')
    name = legislator.text
    vote_type = vote.find('vote').text
    party = legislator.get('party')
    state = legislator.get('state')
    
    if vote_type == 'Yea':
        yay_votes.append((name, party, state))
    elif vote_type == 'Nay':
        nay_votes.append((name, party, state))

# Sort the lists by state
yay_votes = sorted(yay_votes, key=lambda x: x[2])
nay_votes = sorted(nay_votes, key=lambda x: x[2])

# Print the bill being voted upon
print(f"Bill being voted upon: {bill}")

# Print the sorted lists with party affiliation and state
print("\nYay Votes:")
for name, party, state in yay_votes:
    print(f"{name} ({party}, {state})")

print("\nNay Votes:")
for name, party, state in nay_votes:
    print(f"{name} ({party}, {state})")
