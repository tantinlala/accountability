from pydantic import BaseModel

class IndustrySchema(BaseModel):
    industry_codes: list[str]

class IndustryClassifier:
    def __init__(self, assistant, industries):
        """
        Initializes the IndustryClassifier with a list of industry labels.
        If no labels are provided, a default list of industries is used.
        
        Args:
            industries (list): A list of industry categories.
        """
        self.industries = industries
        self.assistant = assistant


    def classify(self, text):
        system_message = "You are an assistant that classifies bill summaries into relevant industries based on their content."
        industry_list = "\n".join([f"{key}: {self.industries[key]}" for key in self.industries.keys()])
        prompt = f"Classify the following bill into the relevant industries. \
            If none are relevant, provide an empty list. Your response should only contain the codes \
                corresponding to relevant industries, not the description. \
                    \n\n{text}\n\nAvailable industries:\n{industry_list}."

        print(prompt)

        industry_classifications = self.assistant.prompt_for_json_response(prompt, IndustrySchema, system_message)
        return industry_classifications 
