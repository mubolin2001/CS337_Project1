import json
import re
from preprocess import preprocess

def official_account(data):
    '''
    Given a dataset of tweet data, extract all official accounts tweets text
    from the tweets.
    :param data: a json file containing all tweets.
    :return: a tuple (trimmed text, official accounts)
    '''
    tweets = preprocess(data)
    res = []
    for tweet in tweets:
        username = tweet.user['screen_name']
        if username is None:
            continue
        else:
            if 'goldenglobes' in username.lower():
                res.append((username, tweet.text))
    return res


if __name__ == "__main__":
    data = 'gg2013.json'
    print(official_account(data))