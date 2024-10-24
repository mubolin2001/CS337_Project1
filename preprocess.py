"""
Preprocess each tweet in the dataset. Store the preprocessed tweets in a list.
"""

import re
import json
import ftfy
from langdetect import detect, LangDetectException
from tweet import Tweet

# def english_only(text):
#     '''
#     Given a dataset of tweet data, remove all non-English tweets.
#     Use langdetect to detect the language of the tweet.
#     :param text: string representing a tweet message.
#     :return: cleaned tweet string.
#     '''
#     detected = detect(text)
#     if detected == 'en':
#         return text

def is_English(text):
    '''
    Given a dataset of tweet data, return True if the tweet is in English.
    Use langdetect to detect the language of the tweet.
    '''
    try:
        if detect(text) == 'en':
            return True
        else:
            return False
    except LangDetectException:
        return False


def extract_hashtags(text):
    '''
    Given a dataset of tweet data, extract all hashtags from the tweets.
    :param text: a string representing a tweet mesaage.
    :return: a tuple (trimmed text, hashtags)
    '''
    hashtags = re.findall(r"#(\w+)", text)  #list of hashtags
    return (re.sub(r'#(\w+)', '', text), hashtags)


def substitute_scrap(data):
    '''
    Given a dataset of tweet data, substitute all scrap characters using ftfy.
    :param data: a string containing tweet message.
    :return: cleaned tweet string.
    '''
    fixed = ftfy.fix_text(data)
    return fixed


def exclude_non_alphanumeric(data):
    '''
    Given a dataset of tweet data, exclude all non-alphanumeric characters.
    Use unidecode to remove all unicode characters to ASCII.
    :param data: a json object representing a tweet.
    :return: cleaned tweet string.
    '''
    return data


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
        text = line['text']
        # if not is_English(text):
        #     continue
        text, hashtags = extract_hashtags(text)
        text = substitute_scrap(text)
        # text = exclude_non_alphanumeric(text)
        # # text = process_url(text)
        # text = exclude_extra_whitespace(text)
        tweet.text = text
        tweet.hashtags = hashtags
        tweet.timestamp = line['timestamp_ms']
        tweet.user = line['user']
        tweet.id = line['id']
        tweet_list.append(tweet)

    return tweet_list

