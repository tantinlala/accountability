import torch
from transformers import pipeline

class IndustryClassifier:
    def __init__(self, candidate_labels):
        """
        Initializes the IndustryClassifier with a list of industry labels.
        If no labels are provided, a default list of industries is used.
        
        Args:
            candidate_labels (list, optional): A list of industry categories.
        """
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
            str: List of industry labels and scores sorted in descending order of score.
        """
        result = self.classifier(text, candidate_labels=self.candidate_labels)

        # Return a list of labels and scores sorted in descending order of score
        result_list = []
        for label, score in zip(result['labels'], result['scores']):
            result_item = dict()
            result_item['label'] = label
            result_item['score'] = score
            result_list.append(result_item)

        return result_list
