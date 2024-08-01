import re
from datetime import datetime
import unicodedata
import nltk
import geonamescache
import unicodedata
import glob
import pandas as pd

import streamlit as st


def find_occurrence_type(headline):
    """ Input is a string that is normally leaded by the occurrence type"""

    # Split the headline at colons ":"
    hl_parts = headline.split(":")

    if len(hl_parts) > 1:
        if len(hl_parts[0]) < 20:
            occurrence_type = hl_parts[0].strip().lower()
        else:
            occurrence_type = None
    else:
        occurrence_type = None
    
    return occurrence_type


def string_to_datetime(date_string):
    """ Converts a date-string like 'Jul 5th 2024 19:41Z' into datetime format. """

    # Remove the ordinal suffix from the day of the month
    day_without_suffix = date_string.replace("rd", "").replace("th", "").replace("st", "").replace("nd", "")

    # Define the format matching the modified date string
    date_format = "%b %d %Y %H:%MZ"

    # Parse the date string into a datetime object
    date_object = datetime.strptime(day_without_suffix, date_format)

    # Return the converted date_string:
    return date_object


def get_author_and_time(phrase):
    """ 
    For a phrase like 'By Simon Hradecky, created Friday, Jul 5th 2024 19:41Z, last updated Friday, Jul 5th 2024 19:41Z' extracts:
    author
    creation date
    last update date
    """

    # Define patterns
    author_pattern = r'By\s+([\w\s]+?),'
    created_pattern = r'created\s\w*,(.+),\slast'
    updated_pattern = r'updated\s\w*,(.+)$'
    

    # Search for author
    author_match = re.search(author_pattern, phrase)
    if author_match:
        author = author_match.group(1).strip()
    else:
        author = None

    # Search for created timestamp
    created_match = re.search(created_pattern, phrase)
    if created_match:
        created_string = created_match.group(1).strip()
        created = string_to_datetime(created_string)
    else:
        created = None

    # Search for updated timestamp
    updated_match = re.search(updated_pattern, phrase)
    if updated_match:
        updated_string = updated_match.group(1).strip()
        updated = string_to_datetime(updated_string)
    else:
        updated = None

    return author, created, updated


def remove_accented_chars(text):
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8', 'ignore')
    return text


def preprocess_text(doc, stop_words, city_names, country_names):

    # lower case and remove special characters\whitespaces
    doc = re.sub(r'[^a-zA-Z\s]', ' ', doc, flags=re.I|re.A) # [^a-zA-Z\s] => remove any digits, special characters, symbols etc.
    doc = doc.lower().strip()

    # tokenize document
    tokens = nltk.word_tokenize(doc)

    # filter stopwords out of document
    filtered_tokens = [token for token in tokens if token not in stop_words]

    # remove 1 and 2 letter words
    cleaned_tokens = [token for token in filtered_tokens if len(token) > 2]

    # Find and print city names in the text
    found_cities = {token for token in cleaned_tokens if token in city_names}
    found_countries = {token for token in cleaned_tokens if token in country_names}

    # remove countries and cities from the text:
    no_geo_tokens = [token for token in cleaned_tokens if token not in found_cities.union(found_countries)]

    # re-create document from filtered tokens
    doc = ' '.join(no_geo_tokens)
    return doc, found_cities, found_countries


def assign_flight_phase(title, text):
    """ Assign a flight phase to a row """

    flight_phases = ["taxi", "takeoff", "climb", "cruise", "enroute", "descending", "approach", "landing", "rollout"]

    #Look for flight phase in the title
    for flight_phase in flight_phases:
        if flight_phase in title:
            return flight_phase

    # If no flight phase in the title, look for the flight phase in the text
    if len(text) > 300:
        text_beginning = text[:300].lower()
    else:
        text_beginning = text.lower()

    for flight_phase in flight_phases:
        if flight_phase in text_beginning:
            return flight_phase
    return "unkown"


def list_to_txt(text_list, txt_file):
    try:
        with open(txt_file, 'w') as file:
            for text in text_list:
                text = re.sub(r'[\n\r\t\s]+', ' ', text, flags=re.UNICODE) # Remove all linebrakes, tabs, etc.
                cleaned_text = text.replace('\n', ' ')
                file.write(f"{cleaned_text}\n")

        print("txt-file created")
        return 1

    except:
        print("There was a problem converting the csv-file to a text-file")

        return 0

def get_from_to_airport(text, city_names):
    if len(text) > 300:
        sentence = text[:300]
    else:
        sentence = text

    # Detect the first "from" if any
    sentence = sentence.split("from", 1)

    if len(sentence) > 1:
        # Take the part of the sentence after "from"
        sentence = sentence[1].strip()

        # Detect "to" if any
        sentence = sentence.split("to", 1)

        if len(sentence) > 1:
            from_ = sentence[0]
            to_ = sentence[1].split(")")[0].strip()
            from_city = None
            to_city = None

            # Find from city and break when found
            for city_name in city_names:
                if city_name in from_:
                    from_city = city_name
                    break

            # Find to city and break when found
            for city_name in city_names:
                if city_name in to_:
                    to_city = city_name
                    break

            return from_city, to_city
        
        else:
            return None, None     
    
    else:
        return None, None
    
    
def load_df(path):
    file_list = glob.glob(path)
    st.write(file_list)

    # Initialize an empty list to store DataFrames
    dataframes = []

    # Loop through the list of files and read each file into a DataFrame
    for file in file_list:
        sub_df = pd.read_csv(file)  # Read the CSV file
        dataframes.append(sub_df)  # Append DataFrame to the list

    # Concatenate all DataFrames in the list into a single DataFrame
    df = pd.concat(dataframes, ignore_index=True)

    return df