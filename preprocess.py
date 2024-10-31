"""
Preprocess each tweet in the dataset. Store the preprocessed tweets in a list.
"""

import re
import json
from tweet import Tweet
from ftfy import fix_text
import unidecode
from langdetect import detect, detect_langs
from concurrent.futures import ProcessPoolExecutor
import pickle
import os

hashtag_pattern = re.compile(r"#(\w+)")
extrawhitespace_pattern = re.compile(r'\s+')
url_pattern = re.compile(r"http\S+")
CACHE_FILE = "cache.pkl"

def english_only(data):
    '''
    Given a dataset of tweet data, remove all non-English tweets.
    Use langdetect to detect the language of the tweet.
    :param data: a json object representing a tweet.
    :return: cleaned tweet string.
    '''
    '''
    find hashtags and remove them first
    then remove non-english tweets
    '''
    text = data["text"]
    try:
        lang = detect(text)
        if lang == 'en':
            return data
        else:
            return None
    except:
        return None

def extract_hashtags(data):
    '''
    Given a dataset of tweet data, extract all hashtags from the tweets.
    :param data: a json object representing a tweet.
    :return: hastags.
    '''
    """
    hastags: #abc or @abc
    """
    text = data["text"]
    hashtags = re.findall(hashtag_pattern, text)
    text = re.sub(extrawhitespace_pattern, " ", text).strip()
    data["text"] = text
    data["hashtags"] = hashtags
    return hashtags

def substitute_scrap(data):
    '''
    Given a dataset of tweet data, substitute all scrap characters using ftfy.
    :param data: a json object representing a tweet.
    :return: cleaned tweet string.
    '''
    data["text"] = fix_text(data["text"])
    return data

def exclude_non_alphanumeric(data):
    '''
    Given a dataset of tweet data, exclude all non-alphanumeric characters.
    Use unidecode to remove all unicode characters to ASCII.
    :param data: a json object representing a tweet.
    :return: cleaned tweet string.
    '''
    text = data["text"]
    text = unidecode.unidecode(text)
    text = re.sub(r'\W+', ' ', text)
    data["text"] = text
    return data

def process_url(data):
    '''
    Given a dataset of tweet data, process all URLs.
    :param data: a json object representing a tweet.
    :return: cleaned tweet string.
    '''
    #remove urls
    text = data["text"]
    text = re.sub(url_pattern, "", text).strip()
    data["text"] = text
    return data

def exclude_extra_whitespace(data):
    '''
    Given a dataset of tweet data, exclude all extra whitespaces. Keep tabs and newlines.
    :param data: a json object representing a tweet.
    :return: cleaned tweet string.
    '''
    fixed = re.sub(extrawhitespace_pattern, ' ', data)
    fixed = " ".join(fixed.split())
    return fixed

def remove_retweets(data):
    '''
    Given a dataset of tweet data, remove all retweets.
    :param data: a json object representing a tweet.
    :return: cleaned tweet string.
    '''
    if data["text"].startswith("RT"):
        return None
    return data

def preprocess_tweet(line):
    substitute_scrap(line)
    process_url(line)
    hashtag = extract_hashtags(line)
    line = remove_retweets(line)
    if line is None:
        return None
    en_tweet = english_only(line)
    if en_tweet:
        tweet = Tweet()
        text = exclude_extra_whitespace(en_tweet["text"])
        tweet.text = text
        tweet.hashtags = hashtag
        tweet.timestamp = line['timestamp_ms']
        tweet.user = line['user']
        tweet.id = line['id']
        return tweet
    return None

def preprocess(file):
    '''
    Given a dataset of tweet data, preprocess the data. Facilitate the functions above
    to complete the task.
    :param file: path of dataset with tweet data.
    :return: list of preprocessed tweets.
    '''
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'rb') as file:
            print("\rLoading cached data...")
            print("\rSkipping preprocessing...")
            
            tweet_list = pickle.load(file)
            print(f"\rNumber of tweets: {len(tweet_list)}")
        return tweet_list

    # Specify the path to your JSON file
    file_path = file

    # Open and load the JSON data
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # Preprocess the data
    tweet_list = []
    print("\rPreprocessing data...")
    with ProcessPoolExecutor() as executor:
        results = list(executor.map(preprocess_tweet, data))

    tweet_list = [tweet for tweet in results if tweet is not None]

    # sort tweets by timestamp
    tweet_list.sort(key=lambda x: x.timestamp)

    with open(CACHE_FILE, 'wb') as cache:
        pickle.dump(tweet_list, cache)
        print("\rTweets saved to cache.")
    
    print("\rPreprocessing complete.")
    print(f"\rNumber of tweets: {len(tweet_list)}")
    return tweet_list

if __name__ == "__main__":
    tweets = preprocess('gg2013.json')
    print("\rPreprocessing complete.")
    print(f"\rNumber of tweets: {len(tweets)}")
    
    for i in range(50):
        print(f'{i}-{tweets[i]}')