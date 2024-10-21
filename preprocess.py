"""
Preprocess each tweet in the dataset. Store the preprocessed tweets in a list.
"""

import re
import json
from tweet import Tweet
from fify import fix_text
import unidecode
from langdetect import detect, detect_langs


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
    hashtags = re.findall(r"#(\w+)", text)
    text = re.sub(r"#(\w+)", "", text).strip()
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
    pass


def process_url(data):
    '''
    Given a dataset of tweet data, process all URLs.
    :param data: a json object representing a tweet.
    :return: cleaned tweet string.
    '''
    pass


def exclude_extra_whitespace(data):
    '''
    Given a dataset of tweet data, exclude all extra whitespaces. Keep tabs and newlines.
    :param data: a json object representing a tweet.
    :return: cleaned tweet string.
    '''
    fixed = re.sub(r'\s+', ' ', data)
    fixed = " ".join(fixed.split())
    return fixed



def preprocess(file):
    '''
    Given a dataset of tweet data, preprocess the data. Facilitate the functions above
    to complete the task.
    :param file: path of dataset with tweet data.
    :return: list of preprocessed tweets.
    '''
    # Specify the path to your JSON file
    file_path = file

    # Open and load the JSON data
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Preprocess the data
    tweet_list = []
    for line in data:
        tweet = Tweet()
        substitute_scrap(line)
        hashtag = extract_hashtags(line)
        en_tweet = english_only(line)
        text = None if en_tweet is None else en_tweet["text"]
        text = exclude_non_alphanumeric(text)
        # text = process_url(text)
        text = exclude_extra_whitespace(text)
        tweet.text = text
        tweet.hashtags = hashtag
        tweet.timestamp = line['timestamp']
        tweet.user = line['user']
        tweet.id = line['id']
        tweet_list.append(tweet)

    return tweet_list

