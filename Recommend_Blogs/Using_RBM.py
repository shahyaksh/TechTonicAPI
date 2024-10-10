# Import necessary libraries
import pandas as pd
from app import cursor, get_user_ratings_in_json_format, ratings_df, rating_path
import numpy as np
import tensorflow as tf
from recommenders.models.rbm.rbm import RBM
from recommenders.datasets.sparse import AffinityMatrix
from recommenders.datasets.python_splitters import numpy_stratified_split
from pytz import timezone
from datetime import datetime
import os

# Load blog data and set paths
blog_data_path = os.path.abspath("BlogData/blog_data.csv")
blog_data = pd.read_csv(blog_data_path)

model_path = os.path.join(os.getcwd(), "model/")
top_k_recommendations_path = os.path.join(os.getcwd(), "RecommendedBlogs/top_k_reco.csv")
top_k_df = pd.read_csv(top_k_recommendations_path)

# Extract the previous recommendation timestamp
old_datetime = top_k_df['timestamp'].values[0]

# Get the current time in 'Asia/Kolkata' timezone
curr_time = datetime.now(timezone("Asia/Kolkata")).strftime('%Y-%m-%d %H:%M:%S')
datetime_obj = datetime.strptime(curr_time, '%Y-%m-%d %H:%M:%S')

# Fetch new user ratings between the last recommendation timestamp and the current time
cursor.execute("SELECT * FROM ratings WHERE timestamp BETWEEN %s AND %s", (old_datetime, datetime_obj))
ratings_list = cursor.fetchall()

# Check if new ratings are available
if not ratings_list:
    print("No new ratings")
else:
    # Convert ratings into JSON format and load them into a DataFrame
    ratings_json = get_user_ratings_in_json_format(ratings_list)
    ratings_df_new = pd.DataFrame(ratings_json, index=None)

    # Drop timestamp column from the new ratings DataFrame
    ratings_df_new.drop(columns=['timestamp'], inplace=True)

    # Concatenate new ratings with the existing ratings DataFrame
    ratings_df = pd.concat([ratings_df, ratings_df_new])
    print(f"Updated ratings shape: {ratings_df.shape}")

    # Remove duplicate ratings and save the updated ratings to CSV
    ratings_df.drop_duplicates(inplace=True)
    ratings_df.to_csv(rating_path, index=False)

    # Define the column names for the AffinityMatrix
    header = {
        "col_user": "userId",
        "col_item": "blog_id",
        "col_rating": "ratings",
    }

    # Generate the affinity matrix based on the updated ratings DataFrame
    affinity_matrix = AffinityMatrix(df=ratings_df, **header)

    # Obtain the sparse matrix representation of the affinity matrix
    X, _, _ = affinity_matrix.gen_affinity_matrix()
    print(f"Affinity Matrix shape: {X.shape}")

    # Split the affinity matrix into training and testing sets
    X_train, X_test = numpy_stratified_split(X)

    # Configure TensorFlow to use the GPU if available
    physical_devices = tf.config.list_physical_devices('GPU')
    print(f"Available GPUs: {physical_devices}")

    if physical_devices:
        try:
            tf.config.experimental.set_memory_growth(physical_devices[0], True)
        except:
            pass

    # Train the RBM model on the GPU
    with tf.device('/gpu:0'):
        # Initialize the RBM model with specified hyperparameters
        model = RBM(
            possible_ratings=np.setdiff1d(np.unique(X_train), np.array([0])),
            visible_units=X_train.shape[1],
            hidden_units=1200,
            training_epoch=30,
            minibatch_size=350,
            keep_prob=0.7,
            with_metrics=True
        )

        # Load the pre-trained model from the given path
        model.load(model_path + 'rbm_model_V4.ckpt')

        # Train the model on the training data
        model.fit(X_train)

    # Define the number of top recommendations to generate
    K = 10

    # Predict the top K recommendations for the test set
    top_k_predictions = model.recommend_k_items(X_test, K)

    # Convert the recommendations to a DataFrame
    predicted_df = pd.DataFrame(data=top_k_predictions)

    # Map the predictions back to blog IDs and user IDs
    top_k_df = affinity_matrix.map_back_sparse(top_k_predictions, kind='prediction')
    test_df = affinity_matrix.map_back_sparse(X_test, kind='ratings')

    # Fill missing predictions with 0
    top_k_df['prediction'].fillna(0, axis=0, inplace=True)

    # Extract blog topics for the recommended blogs
    final_topics = []
    for blog in top_k_df['blog_id'].tolist():
        final_topics.append(blog_data[blog_data['blog_id'] == blog]['topic'].values)

    top_k_df['topic'] = pd.DataFrame(final_topics)

    # Extract blog topics for the rated blogs
    rated_blog_topics = []
    for blog in ratings_df['blog_id'].tolist():
        rated_blog_topics.append(blog_data[blog_data['blog_id'] == blog]['topic'].values)

    ratings_df['topic'] = pd.DataFrame(rated_blog_topics)

    # Save the updated model
    model.save(model_path + 'rbm_model_V4.ckpt')

    # Add the current timestamp to the recommendations DataFrame
    top_k_df['timestamp'] = datetime_obj

    # Save the recommendations to a CSV file
    top_k_df.to_csv(top_k_recommendations_path, index=False)
