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

                if industry == "Unknown":
                    continue

                if industry == "Other":
                    continue

                if industry == "Misc Issues":
                    continue

                if industry == "Non-contribution":
                    continue

                if industry == "Retired":
                    continue

                if industry == "Misc Agriculture":
                    continue

                if industry == "Republican/Conservative":
                    continue

                if industry == "Democratic/Liberal":
                    continue

                if industry == "Leadership PACs":
                    continue

                if industry == "No Employer Listed or Found":
                    continue

                if industry == "Generic Occupation/Category Unknown":
                    continue

                if industry == "Employer Listed/Category Unknown":
                    continue

                if catorder not in catorder_industry:
                    catorder_industry[catorder] = industry
    return catorder_industry
