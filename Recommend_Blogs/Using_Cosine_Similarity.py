import pandas as pd
import nltk
import os
import pathlib
import re
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer, PorterStemmer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Load NLTK stopwords for English
lst_stopwords = stopwords.words('english')


def pre_process_text(text, flg_stemm=False, flg_lemm=True, lst_stopwords=None):
    """
    Preprocesses a given text by converting to lowercase, removing punctuation,
    removing stopwords, and optionally applying stemming or lemmatization.

    Parameters:
    text (str): The text to be pre-processed.
    flg_stemm (bool): If True, apply stemming (default: False).
    flg_lemm (bool): If True, apply lemmatization (default: True).
    lst_stopwords (list): A list of stopwords to remove (default: None).

    Returns:
    str: The cleaned and pre-processed text.
    """
    # Convert text to lowercase and strip any extra whitespace
    text = str(text).lower().strip()

    # Remove punctuation using regular expressions
    text = re.sub(r'[^\w\s]', '', text)

    # Split text into words
    lst_text = text.split()

    # Remove stopwords if provided
    if lst_stopwords is not None:
        lst_text = [word for word in lst_text if word not in lst_stopwords]

    # Apply lemmatization if enabled
    if flg_lemm:
        lemmatizer = WordNetLemmatizer()
        lst_text = [lemmatizer.lemmatize(word) for word in lst_text]

    # Apply stemming if enabled
    if flg_stemm:
        stemmer = PorterStemmer()
        lst_text = [stemmer.stem(word) for word in lst_text]

    # Join the processed words back into a single string
    text = " ".join(lst_text)

    return text


def get_similar_blog(blogs: dict, ratings: dict):
    """
    Recommends blogs based on user ratings and content similarity using cosine similarity.

    Parameters:
    blogs (dict): Dictionary containing blog data (e.g., blog_id, content).
    ratings (dict): Dictionary containing user ratings for blogs (e.g., blog_id, ratings, timestamp).

    Returns:
    list: A list of recommended blog IDs.
    """
    # Define the path to the CSV file containing the blog data
    data_file = os.path.join(pathlib.Path(__file__).parent, "BlogData/blog_data.csv")

    # Read the blog data from the CSV file
    blogs_df = pd.read_csv(data_file)

    # Vectorize the blog content using CountVectorizer (bag-of-words model)
    count_vec = CountVectorizer()
    similarity_matrix = count_vec.fit_transform(blogs_df['clean_blog_content'])

    # Compute cosine similarity between blog content vectors
    cosine_sim = cosine_similarity(similarity_matrix)

    # Convert the ratings dictionary into a DataFrame for easier manipulation
    ratings_df = pd.DataFrame(ratings)
    ratings_df.drop(columns=['timestamp'], inplace=True)  # Drop the timestamp column

    # Select blogs with user ratings >= 0.5
    blogs_to_consider = ratings_df[ratings_df['ratings'] >= 0.5]['blog_id']
    high_rated_blogs = blogs_to_consider.values

    # Filter the blogs DataFrame for high-rated blogs
    rated_blogs = blogs_df[blogs_df['blog_id'].isin(high_rated_blogs)]

    # List to store recommended blog IDs
    recommended_blogs = []

    # Iterate over each high-rated blog
    for blog_id in high_rated_blogs:
        # Get the index of the high-rated blog in the DataFrame
        temp_id = blogs_df[blogs_df['blog_id'] == blog_id].index.values[0]

        # Get blogs that have a cosine similarity score greater than 0.5
        similar_blog_ids = blogs_df[cosine_sim[temp_id] > 0.5]['blog_id'].index.values

        # Add the recommended blog IDs to the list, ensuring no duplicates
        for b_id in similar_blog_ids:
            if b_id not in recommended_blogs:
                recommended_blogs.append(b_id)

    return recommended_blogs
