# TechTonicAPI

TechTonicAPI is a RESTful API designed to power a blog recommendation system. It provides functionality for user registration, login, blog recommendations, and managing likes and favorites for personalized blog experiences.

## Features
- **User Registration and Login**: Allows users to register with a username and email, and log in to access personalized features.
- **Personalized Blog Recommendations**: Recommends blogs to users based on the RBM algorithm, Cosine Similarity, or general blog ratings.
- **Blog Management**: Enables users to view, like, and favorite blogs.
- **User Profile Management**: Allows users to update their profiles and manage their liked/favorite blogs.

## Technologies
- **FastAPI**: Framework for building the API.
- **MySQL**: Database for storing user profiles, blog data, likes, and favorites.
- **Pandas**: Used for blog rating and recommendation functionalities.

---

## Getting Started

### Prerequisites

Make sure you have the following installed:

- Python 3.7+
- MySQL
- Uvicorn

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/shahyaksh/TechTonicAPI.git
   cd TechTonicAPI
   ```

2. **Install dependencies**:
   Create a virtual environment and install required Python packages:
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # On Windows use 'venv\Scripts\activate'
   pip install -r requirements.txt
   ```

3. **Configure Database**:
   Set up your MySQL database and provide connection details in your `app.py` or environment variables.

4. **Start the API**:
   Run the FastAPI server using Uvicorn:
   ```bash
   uvicorn app.main:app --reload
   ```

---

## API Documentation

### Base URL:
Local: `http://127.0.0.1:8000/`

### Endpoints

#### **1. User Registration and Authentication**

- **GET /**  
  - **Description**: Root endpoint returning a welcome message.  
  - **Response**:  
    ```json
    { "message": "Welcome to the Blog API Created by Yaksh Shah" }
    ```

- **POST /register/name/{user_name}/email/{user_email}**  
  - **Description**: Registers a new user.  
  - **Response**: `"User Registration Completed"`

- **GET /login/email/{user_email}**  
  - **Description**: Logs in a user by email.  
  - **Response**:  
    ```json
    {
      "user_id": 1,
      "user_name": "John Doe",
      "user_email": "john@example.com",
      "user_res": "Found"
    }
    ```

- **POST /update/name/{user_name}/id/{user_id}**  
  - **Description**: Updates the user's name.  
  - **Response**: `"User Name Updated"`

- **POST /update/image/{user_pic}/id/{user_id}**  
  - **Description**: Updates the user's profile picture.  
  - **Response**: `"User Profile Pic Updated"`

- **GET /name/{user_name}**  
  - **Description**: Checks if a username is unique.  
  - **Response**: `"unique"` or `"not unique"`

- **GET /image/id/{user_id}**  
  - **Description**: Retrieves the user's profile picture.  
  - **Response**: `{ "user_img": <image_file> }`

---

#### **2. Blog Retrieval**

- **GET /blogs**  
  - **Description**: Retrieves top-rated blogs for homepage (before login).  
  - **Response**: List of blog details.

- **GET /blogs/{user_id}**  
  - **Description**: Retrieves personalized blogs for the homepage (after login).  
  - **Response**: List of blog details.

---

#### **3. Blog Recommendations**

- **GET /recommended/no/activity/blogs**  
  - **Description**: Retrieves recommended blogs for users with no activity.  
  - **Response**: List of recommended blogs.

- **GET /recommend/blogs/using/rbm/{user_id}**  
  - **Description**: Retrieves recommended blogs using the RBM algorithm.  
  - **Response**: List of recommended blogs.

- **GET /recommend/similar/blogs/{user_id}**  
  - **Description**: Retrieves similar blogs using Cosine Similarity.  
  - **Response**: List of recommended blogs.

---

#### **4. Likes and Favorites**

- **GET /like/blogs/{user_id}**  
  - **Description**: Retrieves a list of blogs liked by the user.  
  - **Response**: List of liked blogs or `"res": "Not Found"`

- **GET /favourites/blogs/{user_id}**  
  - **Description**: Retrieves a list of favorite blogs.  
  - **Response**: List of favorite blogs or `"res": "Not Found"`

- **POST /content/seen/user/{user_id}/blog/{blog_id}**  
  - **Description**: Marks a blog as seen by the user.  
  - **Response**: Confirmation message.

- **POST /likes/user/{user_id}/blog/{blog_id}**  
  - **Description**: Likes a blog.  
  - **Response**: `"liked"` or `"Already exist"`

- **DELETE /deletelike/user/{user_id}/blog/{blog_id}**  
  - **Description**: Removes a like from a blog.  
  - **Response**: `"unliked"`

- **POST /favourites/user/{user_id}/blog/{blog_id}**  
  - **Description**: Adds a blog to the favorites list.  
  - **Response**: `"Added to Favourites"` or `"Already exist"`

- **DELETE /removefromfavourites/user/{user_id}/blog/{blog_id}**  
  - **Description**: Removes a blog from the favorites list.  
  - **Response**: `"Removed from Favourites"`

---



## Future Features

- Enhanced recommendation algorithms using machine learning.
- Blog content creation and editing.
- User comment and feedback system for blogs.

---

## Contributing

If you'd like to contribute to the project, feel free to fork the repository and submit a pull request.

---

## License

This project is licensed under the MIT License.
