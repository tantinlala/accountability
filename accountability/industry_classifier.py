from pydantic import BaseModel

class IndustrySchema(BaseModel):
    industry_codes: list[str]

class IndustryClassifier:
    EXCLUDED_INDUSTRIES = [
        "Unknown", "Other", "Misc Issues", "Misc Services", "Misc Defense", 
        "Misc Transport", "Non-contribution", "Retired", "Misc Agriculture", 
        "Republican/Conservative", "Democratic/Liberal", "Leadership PACs", 
        "No Employer Listed or Found", "Generic Occupation/Category Unknown", 
        "Employer Listed/Category Unknown", "Balance Forward", "Misc Energy",
        "Misc Health", "Misc Business", "Misc Finance", "Candidate Self-finance"
    ]

    def __init__(self, assistant, industries: dict):
        """
        Initializes the IndustryClassifier with an assistant and a list of industry labels.
        If no labels are provided, a default list of industries is used.
        
        Args:
            assistant: An assistant instance used for classification.
            industries (list): A list of industry categories.
        """

        # Remove excluded industries from the list
        self.industries = {key: value for key, value in industries.items() if value not in self.EXCLUDED_INDUSTRIES}

        self.assistant = assistant


    def classify(self, text):
        """
        Classifies the given text into relevant industries based on its content.

        Args:
            text (str): The text to be classified.

        Returns:
            list: A list of industry codes relevant to the text.
        """
        system_message = "You are an assistant that classifies bill summaries into relevant industries based on their content."

        industry_list = "\n".join([f"{key}: {self.industries[key]}" for key in self.industries.keys()])
        prompt = f"Classify the following bill into the relevant industries. \
            If none are relevant, provide an empty list. Your response should only contain the codes \
                corresponding to relevant industries, not the description. \
                    \n\n{text}\n\nAvailable industries:\n{industry_list}."

        print(prompt)

        industry_classifications = self.assistant.prompt_for_json_response(prompt, IndustrySchema, system_message)
        return industry_classifications
