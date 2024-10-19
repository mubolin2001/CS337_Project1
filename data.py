import json
from tweet import Tweet
def load_data(filename, load_length = None):
    
    with open(filename, 'r') as file:
        data = json.load(file)
    tweets = []
    for tweet in data:
        new_tweet  = Tweet( id = tweet['id'], text = tweet['text'], user = tweet['user'],
        timestamp = tweet['timestamp_ms'])
        tweets.append(new_tweet)
    return tweets

