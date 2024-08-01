"""
The function takes the existing dataset and scrapes the non-existent events.
It then adds them to the existing set and stores it again in the original place.
"""


import pandas as pd
import re
from tqdm import tqdm
import streamlit as st
import glob
import airportsdata
import pycountry
import time

from scraping_helpers import *
from preprocessing_helpers import *

def get_cities():
    airports = airportsdata.load('IATA')  # key is the IATA location code
    airport_cities = []
    for airport in airports:
        city = airports[airport]["city"]
        if len(city) > 2:
            airport_cities.append(city)

    return airport_cities

def get_countries():
    # Get a list of all countries
    countries = [country.name for country in pycountry.countries]

    return countries



def update(path):
    """ The function takes the filepath to the full dataset and then updates that dataset by scraping the new entries on the webiste"""

    # Load the current available dataset
    old_df = load_df(path)

    
    # Read in the current (non-up-to-date) datset
    print(f"Length of previous df: {len(old_df)}")

    # From the dataset read the href of the first row
    last_href = old_df.iloc[0].href


    """ Scrape missing items """

    # Entry
    URL = "https://avherald.com"

    # Scrape hrefs and titles
    titles, hrefs = tqdm(get_new_titles_and_hrefs(URL, last_href), desc="Loading hrefs") # titles is a dict {title: href}

    # Scrape titles, articles, comments unitl that href
    texts = []
    time_authors = []
    headlines = []
    comment_authors = []
    comments = []
    occurrences = []
    urls = []

    # Initialize the progress bar
    counter = 0
    update_length = len(titles)
    progress_bar = st.progress(counter)
    step = update_length / 100

    for href in tqdm(hrefs, desc="Updating Dataset"):
        # Update the counter for the progress bar
        counter += 1
        # Update the progress bar
        progress_bar.progress(int(counter // step))

        url = URL + href
        page = load_page(url)
        article_text, time_author = get_article(page)
        headline_text, comment_authors_texts, comments_texts = get_comments(page)
        occurrence = find_occurrence_type(headline_text)

        texts.append(article_text)
        time_authors.append(time_author)
        headlines.append(headline_text)
        comment_authors.append(comment_authors_texts)
        comments.append(comments_texts)
        occurrences.append(occurrence)
        urls.append(url)

        # Sleep for 1 second
        time.sleep(1)


    df = pd.DataFrame({
        "title": titles,
        "href": hrefs,
        "text": texts,
        "time_author": time_authors,
        "headline": headlines,
        "comment_authors": comment_authors,
        "comments": comments,
        "occurrence": occurrences,
        "url": urls
    })

    

    """ If there are no updates, return the old_df"""
    if len(df) == 0:
        print("Nothing to update")
        # Reprocess flight phase
        old_df["flight_phase"] = old_df.apply(lambda row: assign_flight_phase(row["title"], row["text"]), axis=1)

        ################################################
        # Write the DataFrame to smaller csv-files
        # Define the chunk size
        chunk_size = 10000

        # Calculate the number of chunks
        num_chunks = len(old_df) // chunk_size + (1 if len(old_df) % chunk_size != 0 else 0)

        # Loop through each chunk and write to a separate CSV file
        for i in range(num_chunks):
            start_row = i * chunk_size
            end_row = (i + 1) * chunk_size
            chunk_df = old_df.iloc[start_row:end_row]
            chunk_df.to_csv(f'{path.rstrip("*.csv")}chunk_{i+1}.csv', sep=',', index=False, header=True, na_rep='NULL', encoding='utf-8')

        # # Verification: Display the number of rows in each chunk
        # for i in range(num_chunks):
        #     chunk_df = pd.read_csv(f'../data/processed/chunk_{i+1}.csv')
        #     print(f'chunk_{i+1}.csv shape: {chunk_df.shape}')
        #################################################
        st.write("Nothing to update")
        return old_df
    else:
        # Print the number of new articles
        print(f"{len(df)} new articles found")



    """Preprocess the update_df"""

    # Apply the function to each value in 'Input' column
    df["author"], df["created"], df["updated"] = zip(*df["time_author"].apply(get_author_and_time))

    # Make sure all items in 'text' column are string
    df['text'] = df['text'].apply(lambda x: str(x) if pd.notna(x) else " ")

    # Remove all linebrakes, tabs, etc. in the texts
    def remove_linebreaks(text):
        return re.sub(r'[\n\r\t\s]+', ' ', text, flags=re.UNICODE)
    df["text"] = df["text"].apply(remove_linebreaks)

    # Ensure necessary NLTK resources are downloaded
    nltk.download('punkt');
    stop_words = nltk.corpus.stopwords.words('english')

    # Get a dictionary of cities and countries
    cities = get_cities()
    countries = get_countries()

    # Extract city and country names
    city_names = [remove_accented_chars(city.lower()) for city in cities]
    country_names = [remove_accented_chars(country.lower()) for country in countries]

    # Apply the preprocess_text function to each row in df["text"] with tqdm progress bar
    tqdm.pandas(desc="Normalizing texts")  # This line enables tqdm support for Pandas apply function
    df["normalized_text"], df["cities"], df["countries"] = zip(*df["text"].progress_apply(lambda x: preprocess_text(x, stop_words, city_names, country_names)))

    # Drop rows where there is no text
    df = df[df["text"].notna()]

    # Get from to
    df["from"], df["to"] = zip(*df["text"].apply(lambda x: get_from_to_airport(x, cities)))

    # Assign the flight phase to each new row
    #df["flight_phase"] = df["text"].apply(assign_flight_phase)
    df["flight_phase"] = df.apply(lambda row: assign_flight_phase(row["title"], row["text"]), axis=1)

    # Concatenate the update_df and the old_df:
    df_new = pd.concat([df, old_df], ignore_index=True)

    # Remove all line breaks, tabs, etc.
    df_new['text'] = df_new['text'].apply(lambda x: re.sub(r'[\n\r\t\s]+', ' ', x, flags=re.UNICODE))

    # Reprocess from-to
    df_new["from"], df_new["to"] = zip(*df_new["text"].apply(lambda x: get_from_to_airport(x, cities)))


    ################################################
    # Write the DataFrame to smaller csv-files
    # Define the chunk size
    chunk_size = 10000

    # Calculate the number of chunks
    num_chunks = len(df_new) // chunk_size + (1 if len(df_new) % chunk_size != 0 else 0)

    # Loop through each chunk and write to a separate CSV file
    for i in range(num_chunks):
        start_row = i * chunk_size
        end_row = (i + 1) * chunk_size
        chunk_df = df_new.iloc[start_row:end_row]
        chunk_df.to_csv(f'{path.rstrip("*.csv")}chunk_{i+1}.csv', sep=',', index=False, header=True, na_rep='NULL', encoding='utf-8')

    # # Verification: Display the number of rows in each chunk
    # for i in range(num_chunks):
    #     chunk_df = pd.read_csv(f'../data/processed/chunk_{i+1}.csv')
    #     print(f'chunk_{i+1}.csv shape: {chunk_df.shape}')
    #################################################

    """ Done with updating """
    print("Update complete")

    return df_new
