import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer, util

import streamlit as st

from search_models import *
from preprocessing_helpers import *
from scraping_helpers import *
from update_dataset import *


def main():
    # Create title and introduction of the project 

    st.write("# Sentence-Transformer-Search on the Aviation Herald Dataset")

    # Show the dataset

    # Read in the dataset
    path = "../data/processed/*.csv"
    # Initialize session state for the dataframe
    if "df" not in st.session_state:
        st.session_state.df = load_df(path)
    
    # Filter the dataset
    flight_phase_options = ["All flight phases"] + list(st.session_state.df["flight_phase"].unique())
    selected_flight_phase = st.selectbox("Select flight phase", flight_phase_options)

    if selected_flight_phase == "All flight phases":
        filtered_df = st.session_state.df
        st.session_state.search_text = ""  # Clear the previous search text
    else:
        filtered_df = st.session_state.df[st.session_state.df.flight_phase == selected_flight_phase]
        st.session_state.search_text = ""  # Clear the previous search text

    # Show the filtered dataframe
    st.dataframe(filtered_df, column_order=("title", "flight_phase", "text", "occurrence", "url"))
    st.write(f"Length of full dataset: {len(st.session_state.df)}")
    st.write(f"Length of filtered dataset: {len(filtered_df)}")
    

    # FastText Similarity search
    st.write("## SentenceTransformer Search")
    st.write("You can paste or describe an aviation occurrence in the field below and the Aviation Herald dataset will be searched for the most similar texts")



    # Initialize session state
    if 'sentence_transformer_model' not in st.session_state:
        st.session_state.sentence_transformer_model = None
    if 'search_text' not in st.session_state:
        st.session_state.search_text = ""
    if "new_text_embeddings" not in st.session_state:
        st.session_state.new_text_embeddings = None
    if "corpus" not in st.session_state:
        st.session_state.corpus = None

    # Button to run the Sentence Transformer embedding:
    if st.button("Create Embeddings"):
        # Clear the search text field
        st.session_state.search_text = ""  # Clear the previous search text

        # Load a pre-trained model from sentence-transformers
        st.session_state.sentence_transformer_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Generate corpus
        st.session_state.corpus = filtered_df.text.tolist()

        # Generate embeddings for the texts
        st.session_state.new_text_embeddings = st.session_state.sentence_transformer_model.encode(st.session_state.corpus)

        

    # Display the text area only if the Sentence-Transformer is initialized
    if st.session_state.sentence_transformer_model:
        st.session_state.search_text = st.text_area(
            label="Your search text",
            value=st.session_state.search_text,  # Ensure the current value is preserved
            height=300,
            max_chars=3000,
            placeholder="Your search text for similarity search"
        )

        top_n = st.slider("Select number of results", 0, 50, 10, 5)
        # Button to submit search text
        if st.button("Submit"):
            if st.session_state.sentence_transformer_model:
                new_text_embedding = st.session_state.sentence_transformer_model.encode([st.session_state.search_text])
                # Compute cosine similarity between the new text and the corpus
                cosine_scores = util.pytorch_cos_sim(new_text_embedding, st.session_state.new_text_embeddings)[0].numpy()

                # Get the indices of the sorted scores in descending order
                sorted_indices = np.argsort(cosine_scores)[::-1]

                # Print the sorted similarity scores and corresponding texts
                print("Texts sorted by similarity to the new text:")
                # Write results to the container
                with st.container():
                    counter = 0
                    for idx in sorted_indices[:top_n]:
                        counter += 1
                        st.write(f"##### Result {counter}")
                        st.write(st.session_state.corpus[idx])
                        st.write(f"Similarity Score: {cosine_scores[idx]:.4f}")
                        st.write(filtered_df.iloc[idx].url)

            else:
                st.error("No embeddings for the corpus created. Please train FastText model first.")



if __name__ == "__main__":
    main()