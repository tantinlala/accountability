import datetime
import os
from accountability.secrets_parser import SecretsParser
from accountability.summarizer import Summarizer
from accountability.openai_assistant import OpenAIAssistant
from accountability.congress_api import CongressAPI
from accountability.hr_roll_call_processor import HRRollCallProcessor
from accountability.congress_database import CongressDatabase


def run_setup_pipeline(template_file, roll_call_id):
    # First, create a secrets parser
    secrets_parser = SecretsParser()

    # Pass the secrets_parser into the constructors for these so that they can tell the parser what secrets they need
    CongressAPI(secrets_parser)
    OpenAIAssistant(secrets_parser)

    # secrets_parser should now know how to create a template secrets file
    secrets_parser.create_template_secrets_file(template_file)

    congress_db = CongressDatabase()

    year = datetime.datetime.now().year
    congress_db.update_hr_roll_call_id(year, roll_call_id)


def run_bill_getting_pipeline(secrets_file, num_days, save_directory):
    # Parse secrets from a file
    secrets_parser = SecretsParser()
    secrets_parser.parse_secrets_file(secrets_file)

    # Allow bill scraper to get required secrets
    bill_scraper = CongressAPI(secrets_parser)

    # Write all data to files
    bill_scraper.save_bills_as_text(num_days, save_directory)

def run_process_most_recently_voted_hr_bills(secrets_file, save_directory):
    # Parse secrets from a file
    secrets_parser = SecretsParser()
    secrets_parser.parse_secrets_file(secrets_file)

    openai_assistant = OpenAIAssistant(secrets_parser)

    bill_scraper = CongressAPI(secrets_parser)
    congress_db = CongressDatabase()
    year = datetime.datetime.now().year

    hr_roll_call_processor = HRRollCallProcessor()
    latest_roll_call_id = congress_db.get_most_recent_hr_roll_call_id(year)

    while True:
        next_roll_call_id = latest_roll_call_id + 1
        hr_roll_call_processor.process_roll_call(year, next_roll_call_id)
        congress = hr_roll_call_processor.get_congress()
        bill_id = hr_roll_call_processor.get_bill_id()
        if bill_id is None:
            print(f"No roll call found for {next_roll_call_id}")
            break

        action_datetime = hr_roll_call_processor.get_action_datetime()

        bill_save_directory = f"{save_directory}/{congress}-{bill_id.replace('/', '-')}"
        if not os.path.exists(bill_save_directory):
            os.makedirs(bill_save_directory)

        bill_file_path = bill_scraper.save_bill_as_text(congress, bill_id, action_datetime, bill_save_directory)

        summarizer = Summarizer(openai_assistant, filename=bill_file_path)
        summarizer.summarize_file(bill_save_directory)

        amendment_file_path = None
        if hr_roll_call_processor.is_amendment_vote():
            amendment_file_path = bill_scraper.save_amendment_as_text(congress, bill_id, action_datetime, bill_save_directory)

        # Save the votes to a .md file as a markdown table
        votes = hr_roll_call_processor.get_votes()

        # Create file path for roll call
        roll_call_file = f"{bill_save_directory}/{action_datetime}-rollcall-{next_roll_call_id}.md"

        with open(roll_call_file, 'w') as file:
            # Get file name from file path
            file_name = os.path.basename(bill_file_path)
            file.write(f"Bill Version File: {file_name}\n\n")
            file.write(f"Roll Call Time: {action_datetime}\n\n")
            file.write(f"Vote Question: {hr_roll_call_processor.get_vote_question()}\n\n")
            if amendment_file_path is not None:
                file.write(f"Amendment File: {os.path.basename(amendment_file_path)}\n\n")

            # Loop through each vote and write to the file as a markdown table
            # Each vote has the following format {'name': name, 'party': party, 'state': state, 'vote': vote_type}
            file.write("| Name | Party | State | Vote |\n")
            file.write("|------|-------|-------|------|\n")
            for vote in votes:
                decision = vote['vote']
                if decision == "No":
                    decision = "Nay"
                elif decision == "Aye":
                    decision = "Yea"

                file.write(f"| {vote['name']} | {vote['party']} | {vote['state']} | {decision} |\n")

        print(f"Saved votes for {next_roll_call_id} to {roll_call_file}")

        latest_roll_call_id = next_roll_call_id


    congress_db.update_hr_roll_call_id(year, latest_roll_call_id)


def run_summarize_pipeline(secrets_file, text_file, save_directory):
    # Parse secrets from a file
    secrets_parser = SecretsParser()
    secrets_parser.parse_secrets_file(secrets_file)

    openai_assistant = OpenAIAssistant(secrets_parser)

    # Allow summarizer to get required secrets
    summarizer = Summarizer(openai_assistant, text_file)

    # Summarize text file
    summarizer.summarize_file(save_directory)

def get_amendment(secrets_file, congress, bill_id, datetime, save_directory):
    secrets_parser = SecretsParser()
    secrets_parser.parse_secrets_file(secrets_file)

    bill_scraper = CongressAPI(secrets_parser)
    bill_scraper.save_amendment_as_text(congress, bill_id, datetime, save_directory)