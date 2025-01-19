import streamlit as st
import altair as alt
from pathlib import Path
import pandas as pd

from search_models import *
from preprocessing_helpers import *
from scraping_helpers import *
from update_dataset import *

 

def main():
    # Create the app in wide format
    st.set_page_config(layout="wide")

    # Create title and introduction of the project 
    st.write("# Occurrence Similarity Search on the Aviation Herald Dataset")
    st.write("##### Final Project of the Part Time Datascience Course at Constructor Academy")
    st.write("###### Author: Laurent Bobay")


    # Read in and show the dataset
    path = "../data/processed/*.csv"
    df = load_df(path)

    # Create a new column with only the year
    df['date'] = pd.to_datetime(df['created'])
    df['year'] = df['date'].dt.year

    if "df" not in st.session_state:
        st.session_state.df = df

    # Filter the dataset:
    # Text input for search
    search_text = st.text_input("Enter text to search:").lower()
    search_words = search_text.split()
    # Create a regex pattern that matches any of the words
    pattern = '|'.join(search_words)

    # Filter the DataFrame based on the search text if provided
    if search_text:
        filtered_df = st.session_state.df[st.session_state.df['text'].str.contains(pattern, case=False, na=False)]
    else:
        filtered_df = st.session_state.df  # No filtering if the search box is empty

    # Read the aircraft list
    aircraft_path = "aircraft_list.csv"
    aircraft_df = pd.read_csv(aircraft_path)
    if "aircraft_df" not in st.session_state:
        st.session_state.aircraft_df = aircraft_df
    st.dataframe(st.session_state.aircraft_df)

    

    st.write("## The Dataset")
    # Show the filtered dataframe
    st.dataframe(filtered_df, column_order=("title", "flight_phase", "from", "to", "text", "occurrence", "url", "created", "year"))

    # Display the length of the dataset:
    st.write(f"Length of the dataset: {len(filtered_df)}")

    # Add a button to update the dataset and reload the page
    if st.button("Update Dataset"):
        update(path)
        df = load_df(path)

        st.session_state.df = df
        st.rerun()


    # Draw Charts

    # Compute and sort flight_phase_counts
    flight_phase_counts = st.session_state.df["flight_phase"].value_counts()

    # If you want to sort by the values in ascending order, use sort_values
    sorted_flight_phase_counts = flight_phase_counts.sort_values(ascending=False)

    # Convert to DataFrame for better control over display
    sorted_flight_phase_df = sorted_flight_phase_counts.reset_index()
    sorted_flight_phase_df.columns = ["Flight Phase", "Count"]

    # Display the sorted bar chart using Altair
    chart = alt.Chart(sorted_flight_phase_df).mark_bar().encode(
        x=alt.X('Flight Phase', sort=None),
        y='Count'
    )

    st.write("## Occurrences by Flight Phase")
    st.altair_chart(chart, use_container_width=True)
        




if __name__ == "__main__":
    main()