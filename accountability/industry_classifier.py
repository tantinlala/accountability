import torch
from transformers import pipeline
import argparse

class IndustryClassifier:
    def __init__(self, candidate_labels=None):
        """
        Initializes the IndustryClassifier with a list of industry labels.
        If no labels are provided, a default list of industries is used.
        
        Args:
            candidate_labels (list, optional): A list of industry categories.
        """
        if candidate_labels is None:
            self.candidate_labels = [
                "Healthcare",
                "Agriculture",
                "Finance",
                "Technology",
                "Education",
                "Manufacturing",
                "Energy",
                "Transportation",
                "Retail",
                "Entertainment",
                "Real Estate",
                "Hospitality",
                "Legal",
                "Marketing",
                "Non-Profit",
                "Government",
                "Telecommunications",
                "Pharmaceuticals",
                "Food and Beverage",
                "Environmental Services",
            ]
        else:
            self.candidate_labels = candidate_labels

        # Initialize the zero-shot classification pipeline with a pre-trained model
        if torch.backends.mps.is_available():
            device = torch.device("mps")
        elif torch.cuda.is_available():
            device = torch.device("cuda")
        else:
            device = torch.device("cpu")

        self.classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli", device=device)

    def classify(self, text):
        """
        Classifies the input text into one of the predefined industry categories.
        
        Args:
            text (str): The text to classify.
        
        Returns:
            str: The industry category with the highest score.
        """
        result = self.classifier(text, candidate_labels=self.candidate_labels)
        return result['labels'][0]  # Return the top predicted industry

# Example usage
if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Classify text into industry categories.")
    parser.add_argument("file_path", type=str, help="Path to the text file containing the sample text.")
    args = parser.parse_args()

    # Read sample text from file
    with open(args.file_path, "r") as file:
        sample_text = file.read()

    classifier = IndustryClassifier()
    industry = classifier.classify(sample_text)
    print(f"The text relates to the industry: {industry}")
