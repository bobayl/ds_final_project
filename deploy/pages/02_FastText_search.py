import streamlit as st

from search_models import *
from preprocessing_helpers import *
from scraping_helpers import *
from update_dataset import *

 

def main():
    # Create title and introduction of the project 

    st.write("# FastText-Search on the Aviation Herald Dataset")

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
    st.write("## FastText Search")
    st.write("You can paste or describe an aviation occurrence in the field below and the Aviation Herald dataset will be searched for the most similar texts")



    # Initialize session state
    if 'fast_text_model' not in st.session_state:
        st.session_state.fast_text_model = None
    if 'search_text' not in st.session_state:
        st.session_state.search_text = ""

    # Button to run the TF-IDF vectorizer
    if st.button("Train FastText model on filtered dataset"):
        # Path to the output text file
        txt_filepath = "../data/interim/text_corpus.txt"
        st.session_state.search_text = ""  # Clear the previous search text
        st.session_state.fast_text_model = train_fasttext(filtered_df, txt_filepath, model='skipgram')
        

    # Display the text area only if the Fasttext model is trained
    if st.session_state.fast_text_model:
        text = st.text_area(
            label="Your search text",
            value=st.session_state.search_text,  # Ensure the current value is preserved
            height=300,
            max_chars=5000,
            placeholder="Your search text for similarity search"
        )
        text = re.sub(r'[\n\r\t\s]+', ' ', text, flags=re.UNICODE) # Remove all linebrakes, tabs, etc.
        st.session_state.search_text = text

        # Slider to select number of results
        top_n = st.slider("Select number of results", 0, 50, 10, 5)

        # Button to submit search text
        if st.button("Submit"):
            if st.session_state.fast_text_model:
                model_path = "../models/fasttext_model.bin"
                # Path to the output text file
                txt_filepath = "../data/interim/text_corpus.txt"
                results, top_indices = fasttext_search(st.session_state.search_text, model_path, txt_filepath, top_n=top_n)
                # Write results to the container
                with st.container():
                    for i, result in enumerate(results):
                        title = filtered_df.iloc[top_indices[i]].title
                        text = filtered_df.iloc[top_indices[i]].text[:800] + "..."
                        url = filtered_df.iloc[top_indices[i]].url
                        st.write(f"##### {title}")
                        st.write(text)
                        st.write(url)
                    
            else:
                st.error("FastText model not trained. Please train FastText model first.")


   




if __name__ == "__main__":
    main()