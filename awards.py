"""
Detect the best actor given a dataset of golden globe tweets.
Not a final version, just a working solution for a specific sub problem.
"""
import re
import spacy
import nltk
import utility
from preprocess import preprocess

def detect_awards(tweets):
    """
    Given a dataset of tweet data, detect the awards issued in the event.
    :param tweets: list of tweet data.
    :return: list of awards.
    """
    awards = {}
    for tweet in tweets:
        if tweet.text is None:
            continue
        for hashtag in tweet.hashtags:
            hashtag = hashtag.lower()
            pattern = r"best[a-zA-Z]*"
            match = re.search(pattern, hashtag, re.IGNORECASE)
            if match:
                award = re.sub(r'best', '', hashtag, flags=re.IGNORECASE)
                if award is None:
                    continue
                if award in awards:
                    awards[award] += 1
                else:
                    awards[award] = 1

    result = []
    for key, value in awards.items():
        if utility.is_stopword(key):
            continue
        if value > 5 and len(key) > 1:
            result.append(key)
            result.sort(key=lambda x: x[1], reverse=True)
    return result


def find_nominees(tweets):
    """
    Given a dataset of tweet data, find the nominees for the awards.
    :param tweets: list of tweet data.
    :return: list of nominees.
    """
    nlp = spacy.load('en_core_web_sm')
    nomination = {}
    awards = detect_awards(tweets)
    for tweet in tweets:
        if tweet.text is None:
            continue
        hashtags = set(tweet.hashtags)
        awards_set = set(awards)
        awards_occur = awards_set.intersection(hashtags)
        if len(awards_occur) == 0:
            continue
        text = tweet.text
        text = text.lower()
        output = nlp(text)
        for ent in output.ents:
            if ent.label_ == 'PERSON':
                for award in awards_occur:
                    if award in nomination:
                        if ent.text in nomination[award]:
                            nomination[award][ent.text] += 1
                        else:
                            nomination[award][ent.text] = 1
                    else:
                        nomination[award] = {ent.text: 1}
    return nomination


if __name__ == "__main__":
    tweets = preprocess('gg2013.json')
    print(detect_awards(tweets))
    print(find_nominees(tweets))



