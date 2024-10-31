"""
Preprocess each tweet in the dataset. Store the preprocessed tweets in a list.
"""

import re
import json
import ftfy
import nltk
from langdetect import detect, LangDetectException
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from tweet import Tweet


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


def tokenize(tweet):
    """
    Given a tweet, tokenize the tweet into words.
    """
    nltk.download('punkt_tab')
    tokens = word_tokenize(tweet.lower())
    tokens = [word for word in tokens if word.isalnum() and word not in stopwords.words('english')]
    return tokens


def exclude_extra_whitespace(data):
    '''
    Given a dataset of tweet data, exclude all extra whitespaces. Keep tabs and newlines.
    :param data: a json object representing a tweet.
    :return: cleaned tweet string.
    '''
    fixed = re.sub(r'\s+', ' ', data)
    fixed = " ".join(fixed.split())
    return fixed



def load_tweets(file):
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
        text, hashtags = extract_hashtags(text)
        text = substitute_scrap(text)

        # Create a Tweet object, append to the list
        tweet.text = text
        tweet.hashtags = hashtags
        tweet.timestamp = line['timestamp_ms']
        tweet.user = line['user']
        tweet.id = line['id']
        tweet_list.append(tweet)

    return tweet_list


# if __name__ == "__main__":
#     line = "Ben Affleck wins the award for Best Director - Motion Picture for Argo. #GoldenGlobes"
#     print(tokenize(line))
