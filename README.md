# Summary 
This python package provides a command line interface with the following functionality:

- Processes all votes (i.e. rollcalls) on legislation (i.e. bills) that have happened in the House of Representatives from a certain point of time onwards.
- Summarizes the bill that was voted upon.
- Downloads the vote positions of each congressperson for all votes.
- Outputs a report providing a summary of the bill and the vote positions of each congressperson on the bill.

# Setup instructions 
1. Make sure you at least have Python 3.9 installed
2. Clone this repository onto your computer
3. Run the following command in the root directory of the repo (preferably in a venv): `pip install -e .`
4. In the environment in which you pip installed the package, run the following script: `accountability_setup -r <rollcall_id>`
   1. This will create a template.yaml file that you should fill in with the api keys needed for this application to work (e.g. the OpenAI API and Congress API)
   2. Google instructions on how to get an api key for each api listed in the template.yaml file
   3. This setup script will also create a congress.db database that stores data needed to keep track of what rollcalls have been processed so far.
5. Fill in the blanks of template.yaml (optionally renaming the file to something else)


# Usage instructions
The following usage instructions assume that you are still in the environment where you pip installed this package (e.g. by running `source venv/bin/activate`)

# Process the most recent HR roll calls
In the directory in which your .yaml file is stored, run `accountability_process_hr_rollcalls -s <name of the .yaml file containing api keys> -d <directory to save results>`

This will create a folder called "rollcalls" under the specified directory storing reports on each rollcall after the rollcall_id that you had passed into the accountability_setup script.

This will also create folders for each bill that had been voted upon storing the original text of the bill version and a generated summary of the bill version.