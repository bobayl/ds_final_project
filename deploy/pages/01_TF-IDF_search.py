import streamlit as st

from search_models import *
from preprocessing_helpers import *
from scraping_helpers import *
from update_dataset import *

 

def main():
    # Create title and introduction of the project 

    st.write("# TF-IDF-Search on the Aviation Herald Dataset")

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
    else:
        filtered_df = st.session_state.df[st.session_state.df.flight_phase == selected_flight_phase]

    # Show the filtered dataframe
    st.dataframe(filtered_df, column_order=("title", "flight_phase", "text", "occurrence", "url"))
    st.write(f"Length of full dataset: {len(st.session_state.df)}")
    st.write(f"Length of filtered dataset: {len(filtered_df)}")

    

    # TF-IDF Similarity search
    st.write("## TF-IDF Similarity Search")
    st.write("You can paste or describe an aviation occurrence in the field below and the Aviation Herald dataset will be searched for the most similar texts")



    # Initialize session state
    if 'tfidf_vectorizer' not in st.session_state:
        st.session_state.tfidf_vectorizer = None
    if 'tfidf_matrix' not in st.session_state:
        st.session_state.tfidf_matrix = None
    if 'search_text' not in st.session_state:
        st.session_state.search_text = ""

    # Button to run the TF-IDF vectorizer
    if st.button("Run TF-IDF Vectorizer"):
        st.session_state.search_text = ""  # Clear the previous search text
        st.session_state.tfidf_vectorizer, st.session_state.tfidf_matrix = train_tfidf(filtered_df)
        

    # Display the text area only if the TF-IDF vectorizer is initialized
    if st.session_state.tfidf_vectorizer is not None:
        text = st.text_area(
            label="Your search text",
            value=st.session_state.search_text,  # Ensure the current value is preserved
            height=300,
            max_chars=3000,
            placeholder="Your search text for similarity search"
        )
        text = re.sub(r'[\n\r\t\s]+', ' ', text, flags=re.UNICODE) # Remove all linebrakes, tabs, etc.
        st.session_state.search_text = text


        # Slider to select number of results
        top_n = st.slider("Select number of results", 0, 50, 10, 5)

        # Button to submit search text
        if st.button("Submit"):
            if st.session_state.tfidf_vectorizer is not None and st.session_state.tfidf_matrix is not None:
                top_indices = tfidf_search(st.session_state.search_text, st.session_state.tfidf_vectorizer, st.session_state.tfidf_matrix, top_n=top_n)
                # container = st.container()
                # container.write(f"Found the following top 10 indices: {top_indices}")
                with st.container():
                    for idx in top_indices:
                        title = filtered_df.iloc[idx].title
                        text = filtered_df.iloc[idx].text[:800]
                        url = filtered_df.iloc[idx].url
                        st.write(f"##### {title}")
                        st.write(text + "...")
                        st.write(url)
                    
            else:
                st.error("TF-IDF Vectorizer not initialized. Please run the TF-IDF Vectorizer first.")

   




if __name__ == "__main__":
    main()