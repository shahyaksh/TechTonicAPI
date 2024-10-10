
from fastapi import FastAPI, HTTPException, status, Response
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector as SqlConnector
import pandas as pd
import time
import os
from datetime import datetime
from pytz import timezone
from Recommend_Blogs.Using_Cosine_Similarity import pre_process_text

# Establishing MySQL Database Connection
while True:
    try:
        mydb = SqlConnector.connect(
            host="HostURL",
            user="UserName",
            password="Password",
            database="blog_recommendation_system"
        )
        cursor = mydb.cursor()
        print("Connection to Database Successful")
        break
    except Exception as error:
        print("Connection to Database Failed")
        print("Error:", error)
        time.sleep(2)

# Initialize FastAPI app
app = FastAPI()

# Configure CORS settings
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load ratings CSV
if os.path.basename(__file__) == '__init__.py':
    rating_path = os.path.join(os.getcwd(), 'app/ratings/blog_ratings_V4.csv')
else:
    rating_path = os.path.join(os.path.abspath(os.path.join(os.getcwd(), os.pardir)), 'app/ratings/blog_ratings_V4.csv')

ratings_df = pd.read_csv(rating_path)


# Helper Functions

def get_like_counts(blog_id: int):
    """
    Fetches the like counts for a blog by combining the database likes and ratings from the CSV file.

    Args:
        blog_id (int): ID of the blog

    Returns:
        counts (int): Total like count
    """
    cursor.execute("SELECT * FROM likes WHERE blog_id=%s", [blog_id])
    likes = cursor.fetchall()
    counts = len(likes)

    blog_list_df = ratings_df[ratings_df['blog_id'] == blog_id]
    like_count = len(blog_list_df[blog_list_df['ratings'] == 1.5].values)
    like_count += len(blog_list_df[blog_list_df['ratings'] == 2].values)
    like_count += len(blog_list_df[blog_list_df['ratings'] == 5].values)

    counts += like_count
    return counts


def get_blogs_in_json_format(blogs_list: list, for_recommendation: bool = False):
    """
    Converts the list of blogs into a JSON format.

    Args:
        blogs_list (list): List of blogs
        for_recommendation (bool): Flag to handle recommendation format

    Returns:
        blog_json (list): List of blogs in JSON format
    """
    blog_json = []

    if for_recommendation:
        for blog in blogs_list:
            blog_dict = {
                "blog_id": blog[0],
                "content": blog[1],
                "topic": blog[2]
            }
            blog_json.append(blog_dict)
        return blog_json
    else:
        for blog in blogs_list:
            cursor.execute('SELECT author_name FROM author WHERE author_id=%s', [blog[1]])
            author_name = cursor.fetchone()[0]
            blog_dict = {
                "blog_id": blog[0],
                "authors": author_name,
                "content_link": blog[4],
                "title": blog[2],
                "content": blog[3],
                "image": blog[5],
                "topic": blog[6],
                "like_count": get_like_counts(blog[0]),
                "scrape_time": blog[7]
            }
            blog_json.append(blog_dict)
        return blog_json


def get_blogs_not_to_consider(user_id: int):
    """
    Retrieves the list of blog IDs that should not be recommended to a user (liked or favorited).

    Args:
        user_id (int): ID of the user

    Returns:
        blog_id_not_to_consider_tuple (tuple): Tuple of blog IDs to exclude from recommendations
    """
    # Get liked and favorited blogs
    cursor.execute("SELECT blog_id FROM likes WHERE user_id=%s", (user_id,))
    liked_blog_list = cursor.fetchall()

    cursor.execute("SELECT blog_id FROM favourites WHERE user_id=%s", (user_id,))
    favourites_blog_list = cursor.fetchall()

    blog_id_not_to_consider_list = []

    # Combine liked and favorited blog IDs
    if liked_blog_list:
        blog_id_not_to_consider_list.extend([blog_id[0] for blog_id in liked_blog_list])
    if favourites_blog_list:
        blog_id_not_to_consider_list.extend(
            [blog_id[0] for blog_id in favourites_blog_list if blog_id[0] not in blog_id_not_to_consider_list])

    return tuple(blog_id_not_to_consider_list)


def add_user_ratings(user_id: int, blog_id: int):
    """
    Adds a user rating for a specific blog.

    Args:
        user_id (int): ID of the user
        blog_id (int): ID of the blog

    Returns:
        str: Response indicating success or if rating already exists
    """
    cursor.execute("SELECT * FROM ratings WHERE blog_id=%s AND user_id=%s", [blog_id, user_id])
    if cursor.fetchone():
        return "Already exist"
    else:
        curr_time = datetime.now(timezone("Asia/Kolkata")).strftime('%Y-%m-%d %H:%M:%S')
        datetime_obj = datetime.strptime(curr_time, '%Y-%m-%d %H:%M:%S')
        cursor.execute("INSERT INTO ratings(user_id, blog_id, rating, timestamp) VALUES (%s, %s, %s, %s)",
                       [user_id, blog_id, 0.5, datetime_obj])
        mydb.commit()
        return "seen"


def update_user_rating(user_id: int):
    """
    Updates user ratings based on likes and favorites.

    Args:
        user_id (int): ID of the user
    """
    curr_time = datetime.now(timezone("Asia/Kolkata")).strftime('%Y-%m-%d %H:%M:%S')
    datetime_obj = datetime.strptime(curr_time, '%Y-%m-%d %H:%M:%S')

    # Update ratings for liked blogs
    cursor.execute("""
        UPDATE ratings SET rating=%s, timestamp=%s 
        WHERE user_id=%s AND blog_id IN 
            (SELECT likes.blog_id FROM likes INNER JOIN ratings 
             ON likes.user_id = ratings.user_id AND likes.blog_id = ratings.blog_id)
    """, [2, datetime_obj, user_id])
    mydb.commit()

    # Update ratings for favorited blogs
    cursor.execute("""
        UPDATE ratings SET rating=%s, timestamp=%s 
        WHERE user_id=%s AND blog_id IN 
            (SELECT favourites.blog_id FROM favourites INNER JOIN ratings 
             ON favourites.user_id = ratings.user_id AND favourites.blog_id = ratings.blog_id)
    """, [3.5, datetime_obj, user_id])
    mydb.commit()

    # Update ratings for blogs that are both liked and favorited
    cursor.execute("""
        UPDATE ratings SET rating=%s, timestamp=%s 
        WHERE user_id=%s AND blog_id IN 
            (SELECT favourites.blog_id FROM favourites 
             INNER JOIN likes ON likes.user_id = favourites.user_id 
             AND likes.blog_id = favourites.blog_id)
    """, [5, datetime_obj, user_id])
    mydb.commit()


def get_user_ratings_in_json_format(ratings_list: list):
    """
    Converts the list of user ratings into a JSON format.

    Args:
        ratings_list (list): List of user ratings

    Returns:
        ratings_json (list): List of ratings in JSON format
    """
    ratings_json = []
    for rating in ratings_list:
        rating_dict = {
            "userId": rating[0],
            "blog_id": rating[1],
            "ratings": rating[2],
            "timestamp": rating[3],
        }
        ratings_json.append(rating_dict)
    return ratings_json


def get_blogs_for_recommendation(recommended_blogs: tuple):
    """
    Fetches recommended blogs and formats them in JSON format.

    Args:
        recommended_blogs (tuple): Tuple of recommended blog IDs

    Returns:
        blogs_json (list): List of blogs in JSON format
    """
    cursor.execute(f'SELECT * FROM blogs WHERE blog_id IN {recommended_blogs}')
    blogs_list = cursor.fetchall()
    blogs_json = get_blogs_in_json_format(blogs_list)
    return blogs_json


def on_start():
    """
    Executes when the application starts. It updates the blog data CSV if new blogs are added.
    """
    cursor.execute("SELECT MAX(blog_id) FROM blogs")
    max_id = cursor.fetchone()

    data_path = os.path.join(os.getcwd(), "Recommend_Blogs/BlogData/blog_data.csv")
    blog_data = pd.read_csv(data_path)
    last_blog_id = blog_data['blog_id'].iloc[-1]

    # Check if new blogs are added and update the blog data CSV
    if max_id[0] > last_blog_id:
        cursor.execute(f'SELECT blog_id, blog_content, topic FROM blogs WHERE blog_id > {last_blog_id}')
        blogs_list = cursor.fetchall()
        blogs_json = get_blogs_in_json_format(blogs_list, for_recommendation=True)
        blog_data_2 = pd.DataFrame(blogs_json)
        blog_data_2.columns = ['blog_id', 'content', 'topic']
        blog_data_2['clean_blog_content'] = blog_data_2['content'].apply(
            lambda x: pre_process_text(x, flg_stemm=False, flg_lemm=True, lst_stopwords=None))
        blog_data = pd.concat([blog_data, blog_data_2], ignore_index=True)
        blog_data.to_csv(data_path, index=False)
