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

                if catorder not in catorder_industry:
                    catorder_industry[catorder] = industry
    return catorder_industry
