import streamlit as st
import altair as alt
from pathlib import Path

from search_models import *
from preprocessing_helpers import *
from scraping_helpers import *
from update_dataset import *

 

def main():
    # Create title and introduction of the project 

    st.write("# Occurrence Similarity Search on the Aviation Herald Dataset")
    st.write("##### Final Project of the Part Time Datascience Course at Constructor Academy")
    st.write("###### Author: Laurent Bobay")
    st.write("## Introduction")
    st.write("Here come the introduction...")


    # Show the dataset

    # Read in the dataset
    # The dataset

    # Construct the relative path to your data file
    path = "../data/processed/chunk_1.csv"
    df = load_df(path)

    

    # Initialize session state for the dataframe
    if "df" not in st.session_state:
        st.session_state.df = df

    st.write("## The Dataset")
    # Show the filtered dataframe
    st.dataframe(st.session_state.df, column_order=("title", "flight_phase", "text", "occurrence", "url", "created"))

    # Display the length of the dataset:
    st.write(f"Length of the dataset: {len(st.session_state.df)}")

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