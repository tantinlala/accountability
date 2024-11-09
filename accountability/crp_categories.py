def process_crp_categories(file_path):
    catorder_industry = {}
    with open(file_path, 'r') as file:
        for line in file:
            if line.startswith("Catcode"):
                continue  # Skip the header line
            parts = line.strip().split('\t')
            if len(parts) > 3:
                catorder = parts[2]
                industry = parts[3].replace('"', '')

                excluded_industries = [
                    "Unknown", "Other", "Misc Issues", "Misc Services", "Misc Defense", 
                    "Misc Transport", "Non-contribution", "Retired", "Misc Agriculture", 
                    "Republican/Conservative", "Democratic/Liberal", "Leadership PACs", 
                    "No Employer Listed or Found", "Generic Occupation/Category Unknown", 
                    "Employer Listed/Category Unknown", "Balance Forward", "Misc Energy",
                    "Misc Health", "Misc Business", "Misc Finance", "Candidate Self-finance"
                ]

                if industry in excluded_industries:
                    continue

                if catorder not in catorder_industry:
                    catorder_industry[catorder] = industry
    return catorder_industry
