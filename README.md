# Summary 
This python package provides a command line interface with the following functionality:

- Download all bills that have been voted upon by the senate within the past x months as .txt files
- Download the vote positions of each senator for each bill
- Ask OpenAI to provide a short summary of a .txt file (e.g. one of the bills downloaded)

# Setup instructions 
1. Make sure you at least have Python 3.9 installed
2. Clone this repository onto your machine
3. Run the following command in the root directory of the repo (preferably in a venv): `pip install -e .`
4. In the environment in which you pip installed the package, run the following script: `accountability_setup`
   1. This will create a template.yml file that you should fill in with the api keys needed for this application to work.
   2. Google instructions on how to get an api key for each api listed in the template.yml file
5. Fill in the blanks of template.yml (optionally renaming the file to something else)


# Usage instructions
The following usage instructions assume that you are still in the environment where you pip installed this package (e.g. via `source venv/bin/activate`)

### Step 1: Download senate bills that had been voted upon during the last few months
In the directory in which your .yml file is stored, run `accountability_get_senate_bills -s <name of the .yml file containing api keys> -m <# of months of data>`

Bills in .txt format will be stored in the same directory in which you ran the command.
In addition, the vote positions of each senator on the bill will be printed to a json file.

### Step 2: Estimate how much it will cost to summarize a bill
In the directory in which you downloaded bills in .txt format, run `accountability_estimate_summary_cost -t <name of the bill .txt file>`

### Step 3: Have OpenAI provide a short summary of one of the bills that was downloaded
In the directory in which you downloaded bills in .txt format, run `accountability_summarize -s <name of the .yml file containing api keys> -t <name of the bill .txt file>`

A summary in .txt format will be stored in the same directory in which you ran the command.