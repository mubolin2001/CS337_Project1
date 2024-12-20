from collections import defaultdict
from datetime import datetime
from tweet import Tweet
import pickle
import os
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
import numpy as np

def cluster_tweets_kmeans(tweets, k):
    """
    Clusters tweets using K-means based on their timestamps.

    Parameters:
        tweets (list): A list of Tweet objects, sorted by timestamp.
        k (int): The number of clusters.

    Returns:
        dict: A dictionary with cluster labels as keys and lists of tweets as values.
    """
    # Convert tweet timestamps to a numerical format (seconds since epoch)
    timestamps = np.array([tweet.timestamp for tweet in tweets]).reshape(-1, 1)

    # Apply K-means clustering
    kmeans = KMeans(n_clusters=k, random_state=0)
    kmeans.fit(timestamps)

    # Create a dictionary to store clusters
    clusters = {i: [] for i in range(k)}

    # Assign tweets to their corresponding cluster
    for i, label in enumerate(kmeans.labels_):
        clusters[label].append(tweets[i])

    return clusters

def cluster_by_timestamp(tweets, time_interval='hour'):
    """
    Cluster tweets by their timestamps.
    
    Parameters:
        tweets (list): A list of Tweet objects.
        time_interval (str): The interval for clustering ('hour', 'day').
    
    Returns:
        dict: A dictionary where keys are time intervals and values are lists of tweets.
    """
    clustered_tweets = defaultdict(list)

    for tweet in tweets:
        # Convert string timestamp to datetime object if necessary
        # tweet.timestamp is in ms
        tweet_time = datetime.fromtimestamp(tweet.timestamp / 1000.0)
        
        # Determine the time cluster key
        """if time_interval == 'hour':
            # Use the hour as the key
            key = tweet_time.replace(minute=0, second=0, microsecond=0)
        elif time_interval == 'day':
            # Use the date as the key
            key = tweet_time.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            raise ValueError("Invalid time_interval. Use 'hour' or 'day'.")"""
        if tweet_time.minute < 30:
            key = tweet_time.replace(minute=0, second=0, microsecond=0)
        else:
            key = tweet_time.replace(minute=30, second=0, microsecond=0)

        # Append the tweet to the corresponding cluster
        clustered_tweets[key].append(tweet)

    return clustered_tweets 

def visualize(clustered_tweets):
    timestamp = sorted(clustered_tweets.keys())
    tweet_count = [len(clustered_tweets[key]) for key in timestamp]

    # Create the line plot
    plt.figure(figsize=(12, 6))
    plt.plot(timestamp, tweet_count, marker='o', linestyle='-')
    plt.title('Number of Tweets Over Time')
    plt.xlabel('Time')
    plt.ylabel('Number of Tweets')
    plt.xticks(rotation=45)
    plt.grid()
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
        if os.path.exists("cache.pkl"):
                with open("cache.pkl", "rb") as file:
                        tweets = pickle.load(file)
                        clustered_tweets = cluster_by_timestamp(tweets, time_interval='hour')
                        print(f'number of clusters: {len(clustered_tweets)}')
                        visualize(clustered_tweets)

                        clustered_tweets_kmeans = cluster_tweets_kmeans(tweets, k=32)
                        print(f'number of clusters: {len(clustered_tweets_kmeans)}')
                        visualize(clustered_tweets_kmeans)
                        

        


