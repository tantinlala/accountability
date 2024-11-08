from sentence_transformers import SentenceTransformer, CrossEncoder, util
import numpy as np
import argparse
import nltk
from nltk.tokenize import sent_tokenize
import torch

class BillIndustryAnalyzer:
    def __init__(self, bi_encoder_model='multi-qa-MiniLM-L6-cos-v1', cross_encoder_model='cross-encoder/ms-marco-MiniLM-L-6-v2'):
        # Initialize bi-encoder and cross-encoder models
        self.bi_encoder = SentenceTransformer(bi_encoder_model)
        self.cross_encoder = CrossEncoder(cross_encoder_model)

    def segment_text(self, text):
        # Split text into sentences without limiting to a segment length
        nltk.download('punkt')
        sentences = sent_tokenize(text)
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if ':' in sentence:
                sentence = sentence.split(':')[0]

            if len(sentence) > 2:
                cleaned_sentences.append(sentence)

        return cleaned_sentences 

    def compute_embeddings(self, segments):
        # Compute embeddings for a list of texts
        return self.bi_encoder.encode(segments, convert_to_tensor=True, show_progress_bar=True)

    def analyze_bill(self, text, query):
        # Segment the text
        passages = self.segment_text(text)

        # Compute embeddings for segments and industry keywords
        passages_embeddings = self.bi_encoder.encode(passages, convert_to_tensor=True, show_progress_bar=True)
        query_embedding = self.bi_encoder.encode(query, convert_to_tensor=True, show_progress_bar=True)

        # Retrieve relevant segments using cosine similarity
        hits = util.semantic_search(query_embedding, passages_embeddings)
        hits = hits[0]

        # Re-rank the retrieved segments
        retrieved_segments = [passages[hit['corpus_id']] for hit in hits]
        ranks = self.cross_encoder.rank(query, retrieved_segments)

        print(retrieved_segments)
        print(ranks)

        for rank in ranks:
            print(f"Score: {rank['score']} / Segment: {retrieved_segments[rank['corpus_id']]}")

        return ranks 

    def determine_relevance(self, re_ranked_segments, threshold=0.5):
        # Determine if the bill is relevant to the industry based on the average score
        if len(re_ranked_segments) == 0:
            return False, 0.0
        max_score = max([rank['score'] for rank in re_ranked_segments])
        return max_score >= threshold, max_score

if __name__ == '__main__':
    # Initialize the analyzer
    analyzer = BillIndustryAnalyzer()

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Analyze a bill for industry relevance.')
    parser.add_argument('bill_file', type=str, help='Path to the bill text file')
    args = parser.parse_args()

    # Read the bill text from the file
    with open(args.bill_file, 'r') as file:
        bill_text = file.read()

    query = "government"

    # Analyze the bill
    re_ranked_segments = analyzer.analyze_bill(bill_text, query)

    # Determine relevance
    is_relevant, avg_score = analyzer.determine_relevance(re_ranked_segments)

    if is_relevant:
        print(f"The bill is relevant to the industry with a max relevance score of {avg_score:.2f}.")
    else:
        print(f"The bill is not relevant to the industry. Max relevance score: {avg_score:.2f}.")
