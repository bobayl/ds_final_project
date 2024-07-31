import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from IPython.display import display, Markdown
from tqdm import tqdm
import streamlit as st

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import fasttext

from preprocessing_helpers import list_to_txt


def train_tfidf(df):
    """ Train the tfidf-model"""

    print("training tf-idf")
    print(len(df))
    # Ensure all items in 'text' column are string
    df['normalized_text'] = df['normalized_text'].apply(lambda x: str(x) if pd.notna(x) else '')

    # Create the corpus to search for
    norm_corpus = df.normalized_text.tolist()

    # Tf-Idf vectorization
    tv = TfidfVectorizer(min_df=0., max_df=1., norm='l2', use_idf=True)
    tv_matrix = tv.fit_transform(norm_corpus)
    tv_matrix = tv_matrix.toarray()

    print("done training")
    return tv, tv_matrix
    

def tfidf_search(search_text, tv, tv_matrix, top_n=10):
    """ 
    The function takes a dataframe with the column 'normalized_text' and performs a tfidf-similarity search on it.
    It returns then the top_n similar occurrences from the dataset (optional, default is 10).
    """

    # Transform the new text using the same vectorizer
    search_text_vector = tv.transform([search_text]).toarray()

    # Compute the cosine similarity between the new text and the corpus
    similarity_scores = cosine_similarity(search_text_vector, tv_matrix).flatten()
    print(len(similarity_scores))

    # Get the indices of the top n similarity scores
    top_indices = similarity_scores.argsort()[-top_n:][::-1]

    return top_indices




def train_fasttext(df, txt_filepath, model='skipgram'):
    """ Train the fasttext model"""
   
    # Create the text corpus
    print("Creating text corpus...")
    texts = df.text.tolist()
    list_to_txt(texts, txt_filepath)

    try:
        # Train a FastText model on the corpus
        model = fasttext.train_unsupervised(txt_filepath, model=model, verbose=2)
    except:
        print("An error occurred during training of the model.")
        return 0

    # Save the model
    try:
        model_path = "../models/fasttext_model.bin"
        model.save_model(model_path)
    except:
        print("An error occurred during saving of the model.")
        return 0

    print("Fasttext model training complete.")
    return 1


def fasttext_search(search_text, model_path, txt_filepath, top_n):
    """ 
    The function takes a dataframe with the column 'normalized_text' and performs a fasttext-similarity search on it.
    It returns then the top_n similar occurrences from the dataset (optional, default is 10).
    """

    # Load the trained model
    model = fasttext.load_model(model_path)

    # Read the corpus and generate embeddings
    corpus_file = txt_filepath
    embeddings = []
    texts = []

    with open(corpus_file, 'r') as f:
        for line in f:
            text = line.strip()
            texts.append(text)
            embeddings.append(model.get_sentence_vector(text))

    # Convert to numpy array for easier manipulation
    embeddings = np.array(embeddings)

    # Find similar texts to the search_text
    new_embedding = model.get_sentence_vector(search_text)
    similarities = cosine_similarity([new_embedding], embeddings)[0]
    similar_indices = similarities.argsort()[-top_n:][::-1]
    
    return [(texts[i], similarities[i]) for i in similar_indices], similar_indices

