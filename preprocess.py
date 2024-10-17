import re


def english_only(data):
    '''
    Given a dataset of tweet data, remove all non-English tweets.
    Use langdetect to detect the language of the tweet.
    :param data:
    :return:
    '''
    pass


def extract_hashtags(data):
    '''
    Given a dataset of tweet data, extract all hashtags from the tweets.
    :param data:
    :return:
    '''
    pass


def substitute_scrap(data):
    '''
    Given a dataset of tweet data, substitute all scrap characters using ftfy.
    :param data:
    :return:
    '''
    pass


def exclude_non_alphanumeric(data):
    '''
    Given a dataset of tweet data, exclude all non-alphanumeric characters.
    Use unidecode to remove all unicode characters to ASCII.
    :param data:
    :return:
    '''
    pass


def process_url(data):
    '''
    Given a dataset of tweet data, process all URLs.
    :param data:
    :return:
    '''
    pass


def exclude_extra_whitespace(data):
    '''
    Given a dataset of tweet data, exclude all extra whitespaces. Keep tabs and newlines.
    :param data:
    :return:
    '''
    fixed = re.sub(r'\s+', ' ', data)
    fixed = " ".join(fixed.split())



def preprocess(data):
    '''
    Given a dataset of tweet data, preprocess the data. Facilitate the functions above
    to complete the task.
    :param data:
    :return:
    '''