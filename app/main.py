import os
from app import *
from Recommend_Blogs import Using_Cosine_Similarity


@app.get('/')
async def root():
    """
    Root endpoint that returns a welcome message.
    """
    return {"message": "Welcome to the Blog API Created by Yaksh Shah"}


@app.post('/register/name/{user_name}/email/{user_email}')
async def register_user(user_name: str, user_email: str):
    """
    Registers a new user with the given name and email.
    A default profile picture is used during registration.

    Args:
        user_name (str): The name of the user.
        user_email (str): The email of the user.

    Returns:
        str: Confirmation message on successful registration.
    """
    user_query = ''' INSERT INTO user_profile(user_name, user_email, user_pic)
                     VALUES (%s, %s, %s) '''
    user_info = (user_name, user_email, 'default_profile_pic.jpg')
    cursor.execute(user_query, user_info)
    mydb.commit()
    return "User Registration Completed"


@app.get('/login/email/{user_email}')
async def user_login(user_email: str):
    """
    Logs in a user using their email and retrieves their user details.

    Args:
        user_email (str): The email of the user.

    Returns:
        dict: User details or a message if the user is not found.
    """
    cursor.execute(''' SELECT user_id, user_name, user_email FROM user_profile 
                       WHERE user_email=%s''', [user_email])
    resp = cursor.fetchone()
    if resp is not None:
        user_details = {'user_id': resp[0], 'user_name': resp[1], 'user_email': resp[2], "user_res": "Found"}
        update_user_rating(user_details['user_id'])
        return user_details
    else:
        return {"user_res": "Not Found"}


@app.post('/update/name/{user_name}/id/{user_id}')
async def update_user_name(user_name: str, user_id: int):
    """
    Updates the name of the user with the given user ID.

    Args:
        user_name (str): New user name.
        user_id (int): User ID.

    Returns:
        str: Confirmation message on successful update.
    """
    cursor.execute(""" UPDATE user_profile SET user_name=%s WHERE user_id=%s""",
                   [user_name, user_id])
    mydb.commit()
    return "User Name Updated"


@app.post('/update/image/{user_pic}/id/{user_id}')
async def update_user_profile_pic(user_pic: str, user_id: int):
    """
    Updates the profile picture of the user with the given user ID.

    Args:
        user_pic (str): New profile picture file name.
        user_id (int): User ID.

    Returns:
        str: Confirmation message on successful update.
    """
    cursor.execute(""" UPDATE user_profile SET user_pic=%s WHERE user_id=%s""",
                   [user_pic, user_id])
    mydb.commit()
    return "User Profile Pic Updated"


@app.get('/name/{user_name}')
async def verify_user_name(user_name: str):
    """
    Verifies if a user name is unique.

    Args:
        user_name (str): The user name to check.

    Returns:
        str: "unique" if the name is unique, otherwise "not unique".
    """
    cursor.execute(''' SELECT user_name FROM user_profile 
                       WHERE user_name=%s''', [user_name])
    result = cursor.fetchone()
    if result:
        return "not unique"
    else:
        return "unique"


@app.get('/image/id/{user_id}')
async def get_user_profile_pic(user_id: int):
    """
    Retrieves the profile picture of the user with the given user ID.

    Args:
        user_id (int): User ID.

    Returns:
        dict: The profile picture file name.
    """
    cursor.execute(""" SELECT user_pic FROM user_profile WHERE user_id=%s""", [user_id])
    resp = cursor.fetchone()
    return {"user_img": resp[0]}


@app.get('/blogs')
async def get_blogs_for_home_before_login():
    """
    Retrieves top-rated blogs for the homepage (before login).

    Returns:
        list: A list of blog details in JSON format.
    """
    on_start()
    top_rated_blogs = ratings_df[ratings_df['ratings'] <= 3.5].value_counts().head(30000)
    top_blog_ids = list(set([x[0] for x in top_rated_blogs.index]))
    cursor.execute(f""" SELECT * FROM blogs WHERE blog_id IN {tuple(top_blog_ids)} ORDER BY RAND() LIMIT 30""")
    blogs_list = cursor.fetchall()
    return get_blogs_in_json_format(blogs_list)


@app.get('/blogs/{user_id}')
async def get_blogs_for_home_after_login(user_id: int):
    """
    Retrieves personalized blogs for the homepage (after login).

    Args:
        user_id (int): User ID.

    Returns:
        list: A list of blog details in JSON format.
    """
    blog_id_not_to_consider_tuple = get_blogs_not_to_consider(user_id)
    if blog_id_not_to_consider_tuple is not None:
        cursor.execute(f""" SELECT * FROM blogs WHERE blog_id ORDER BY RAND() LIMIT 30""")
    else:
        cursor.execute(f""" SELECT * FROM blogs WHERE blog_id NOT IN {blog_id_not_to_consider_tuple} 
                             ORDER BY RAND() LIMIT 30""")
    blogs_list = cursor.fetchall()
    return get_blogs_in_json_format(blogs_list)


@app.get('/recommended/no/activity/blogs')
async def get_recommended_blogs_for_user_with_no_activity():
    """
    Retrieves top-rated recommended blogs for users with no activity.

    Returns:
        list: A list of recommended blog details in JSON format.
    """
    top_rated_blogs = ratings_df[ratings_df['ratings'] > 3.5].value_counts().head(30000)
    top_blog_ids = list(set([x[0] for x in top_rated_blogs.index]))
    cursor.execute(f""" SELECT * FROM blogs WHERE blog_id IN {tuple(top_blog_ids)} ORDER BY RAND() LIMIT 20""")
    blogs_list = cursor.fetchall()
    return get_blogs_in_json_format(blogs_list)


@app.get('/recommend/blogs/using/rbm/{user_id}')
async def get_recommended_blogs_using_rbm(user_id: int):
    """
    Retrieves blog recommendations using the RBM algorithm for the given user ID.

    Args:
        user_id (int): User ID.

    Returns:
        list: A list of recommended blog details in JSON format.
    """
    path = os.path.abspath('Recommend_Blogs/RecommendedBlogs/top_k_reco.csv')
    top_reco_df = pd.read_csv(path)
    top_reco_list = top_reco_df[top_reco_df['userId'] == user_id]['blog_id'].values
    cursor.execute(f""" SELECT * FROM blogs WHERE blog_id IN {tuple(top_reco_list)}""")
    blog_list = cursor.fetchall()
    return get_blogs_in_json_format(blog_list)


@app.get('/recommend/similar/blogs/{user_id}')
async def get_recommended_blogs_using_cosine_similarity(user_id: int):
    """
    Retrieves blog recommendations using Cosine Similarity for the given user ID.

    Args:
        user_id (int): User ID.

    Returns:
        list: A list of recommended blog details in JSON format.
    """
    cursor.execute('SELECT * FROM ratings WHERE user_id=%s', [user_id])
    ratings_list = cursor.fetchall()
    ratings_json = get_user_ratings_in_json_format(ratings_list)
    if len(ratings_json) < 3:
        return []
    else:
        blogs_json = []
        recommended_blogs = Using_Cosine_Similarity.get_similar_blog(blogs_json, ratings_json)
        return get_blogs_for_recommendation(tuple(recommended_blogs))


@app.get('/like/blogs/{user_id}')
async def get_liked_blogs(user_id: int):
    """
    Retrieves a list of blogs liked by the user with the given user ID.

    Args:
        user_id (int): User ID.

    Returns:
        list or dict: A list of liked blogs in JSON format or a message if none are found.
    """
    cursor.execute(""" SELECT blog_id FROM likes WHERE user_id=%s""", (user_id,))
    liked_blogs = cursor.fetchall()
    blog_id_tuple = ()
    blog_id_list = []
    blog_json = []

    if liked_blogs:
        for id in liked_blogs:
            blog_id_list.append(id[0])
        blog_id_tuple = tuple(blog_id_list)
        if len(blog_id_tuple) > 1:
            cursor.execute(f""" SELECT * FROM blogs WHERE blog_id IN {blog_id_tuple}""")
        else:
            cursor.execute(f""" SELECT * FROM blogs WHERE blog_id={blog_id_tuple[0]}""")
        blogs_list = cursor.fetchall()
        blog_json = get_blogs_in_json_format(blogs_list)
        return blog_json
    else:
        return {"res": "Not Found"}


@app.get('/favourites/blogs/{user_id}')
async def get_favourites_blogs(user_id: int):
    """
    Retrieves a list of favorite blogs for the user with the given user ID.

    Args:
        user_id (int): User ID.

    Returns:
        list or dict: A list of favorite blogs in JSON format or a message if none are found.
    """
    cursor.execute("SELECT blog_id FROM favourites WHERE user_id=%s", (user_id,))
    favourites_blogs = cursor.fetchall()
    blog_id_tuple = ()
    blog_id_list = []

    if favourites_blogs:
        for id in favourites_blogs:
            blog_id_list.append(id[0])
        blog_id_tuple = tuple(blog_id_list)
        if len(blog_id_tuple) > 1:
            cursor.execute(f""" SELECT * FROM blogs WHERE blog_id IN {blog_id_tuple}""")
        else:
            cursor.execute(f""" SELECT * FROM blogs WHERE blog_id={blog_id_tuple[0]}""")
        blogs_list = cursor.fetchall()
        return get_blogs_in_json_format(blogs_list)
    else:
        return {"res": "Not Found"}


@app.post('/content/seen/user/{user_id}/blog/{blog_id}')
async def seen_blog_content(user_id: int, blog_id: int):
    """
    Marks a blog as seen for the user with the given user ID.

    Args:
        user_id (int): User ID.
        blog_id (int): Blog ID.

    Returns:
        str: Confirmation message.
    """
    return add_user_ratings(user_id, blog_id)


@app.post('/likes/user/{user_id}/blog/{blog_id}')
async def like_blog(user_id: int, blog_id: int):
    """
    Likes a blog for the user with the given user ID, if not already liked.

    Args:
        user_id (int): User ID.
        blog_id (int): Blog ID.

    Returns:
        str: Confirmation message or "Already exist" if the blog is already liked.
    """
    cursor.execute(""" SELECT * FROM likes WHERE blog_id=%s AND user_id=%s""", [blog_id, user_id])
    if cursor.fetchone():
        return "Already exist"
    else:
        curr_time = datetime.now(timezone("Asia/Kolkata")).strftime('%Y-%m-%d %H:%M:%S')
        datetime_obj = datetime.strptime(curr_time, '%Y-%m-%d %H:%M:%S')
        cursor.execute(""" INSERT INTO likes(user_id, blog_id, date_created) VALUES (%s, %s, %s)""",
                       [user_id, blog_id, datetime_obj])
        mydb.commit()
        add_user_ratings(user_id, blog_id)
        return "liked"


@app.delete('/deletelike/user/{user_id}/blog/{blog_id}')
async def unlike_blog(user_id: int, blog_id: int):
    """
    Removes a like from a blog for the user with the given user ID.

    Args:
        user_id (int): User ID.
        blog_id (int): Blog ID.

    Returns:
        str: Confirmation message.
    """
    cursor.execute(""" DELETE FROM likes WHERE user_id=%s AND blog_id=%s""", (user_id, blog_id))
    mydb.commit()
    return "unliked"


@app.post('/favourites/user/{user_id}/blog/{blog_id}')
async def add_blog_to_favourites(user_id: int, blog_id: int):
    """
    Adds a blog to the favorites list for the user with the given user ID, if not already in favorites.

    Args:
        user_id (int): User ID.
        blog_id (int): Blog ID.

    Returns:
        str: Confirmation message or "Already exist" if the blog is already in favorites.
    """
    cursor.execute(""" SELECT * FROM favourites WHERE blog_id=%s AND user_id=%s""", [blog_id, user_id])
    if cursor.fetchone():
        return "Already exist"
    else:
        cursor.execute(""" INSERT INTO favourites(user_id, blog_id) VALUES (%s, %s)""", [user_id, blog_id])
        mydb.commit()
        add_user_ratings(user_id, blog_id)
        return "Added to Favourites"


@app.delete('/removefromfavourites/user/{user_id}/blog/{blog_id}')
async def remove_blog_from_favourites(user_id: int, blog_id: int):
    """
    Removes a blog from the favorites list for the user with the given user ID.

    Args:
        user_id (int): User ID.
        blog_id (int): Blog ID.

    Returns:
        str: Confirmation message.
    """
    cursor.execute(""" DELETE FROM favourites WHERE user_id=%s AND blog_id=%s""", (user_id, blog_id))
    mydb.commit()
    return "Removed from Favourites"

# To run the application:
# uvicorn app.main:app --reload
