#TODO: get ProPublica api key

#TODO: download all bills up to 3 months that isn't presently in database


#TODO: find all bills voted upon in last 6 months by both senate and house

#TODO: filter out votes to only include bills of interest
# - only include votes with a bill api_uri: use this as the unique key
# - only include latest vote on latest version of a bill (for now)
# - only include the following question types:
# QUESTION_TYPES = ["On Passage of the Bill",
#                   "On Passage",
#                   "On the Cloture Motion",
#                   "On Cloture on the Motion to Proceed",
#                   "On the Joint Resolution",
#                   "On the Motion to Proceed",
#                   "On the Motion"]

#TODO: download text of all unique bills
# - replace using congress api with ProPublica api
# https://projects.propublica.org/api-docs/congress-api/
# go through unique bills that are left in the list and download xml (base this on latest date before vote date of version)
# https://www.senate.gov/legislative/KeytoVersionsofPrintedLegislation.htm

class BillScraper:
    SECRET_GROUP = 'propublica'
    SECRET_NAME = 'PROPUBLICA_API_KEY'

    def __init__(self, secrets_parser):
        self.secret_ = secrets_parser.get_secret(self.SECRET_GROUP, self.SECRET_NAME)
