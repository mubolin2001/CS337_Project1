"""
Detect the best actor given a dataset of golden globe tweets.
Not a final version, just a working solution for a specific sub problem.
"""
import re
import spacy
import nltk
from imdb import Cinemagoer
import wordninja
from nltk import word_tokenize, SnowballStemmer, WordNetLemmatizer, pos_tag
from nltk.corpus import stopwords
from rapidfuzz import fuzz
from preprocess import load_tweets

nlp = spacy.load('en_core_web_sm')
ia = Cinemagoer()
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('stopwords')


# Initialize NLP tools
stemmer = SnowballStemmer("english")  # Using SnowballStemmer for better performance
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))


def process_text(text):
    """
    Given a text, preprocess the text by normalizing, stemming and removing stopwords.
    :param text: a string representing a tweet message.
    :return: a string representing the processed text.
    """
    tokens = word_tokenize(text.lower())
    tokens = [lemmatizer.lemmatize(word) for word in tokens if word.isalnum() and word not in stop_words]
    stemmed_words = [
        word if pos_tag([word])[0][1] in ['NNP', 'NNPS'] else stemmer.stem(word)  # Skip proper nouns
        for word in tokens
    ]
    return ' '.join(stemmed_words)


def extract_awards(tweets):
    award_mentions = {}
    for tweet in tweets:
        doc = nlp(tweet)
        for chunk in doc.noun_chunks:
            if "award" in chunk.text.lower() or "best" in chunk.text.lower():
                award = chunk.text.lower().strip()
                if award in award_mentions:
                    award_mentions[award] += 1
                else:
                    award_mentions[award] = 1
    # Filtering awards based on frequency threshold (arbitrary value, could vary)
    return [award for award, count in award_mentions.items() if count > 3]



def find_nominees(text):
    """
    Given a tweet text, find the nominees for the awards.
    :param tweets: list of tweet data.
    :return: list of nominees.
    """
    if text is None:
        return []
    doc = nlp(text)
    nominees = []
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            nominees.append(ent.text)
        elif ent.label_ == "WORK_OF_ART":
            movie = match_films_with_imdb(ent.text)
            if movie:
                nominees.append(movie)
    return nominees


def match_films_with_imdb(text):
    results = ia.search_movie(text)
    if results:
        return results[0]['title'].lower()
    return None


def find_person(text):
    if text is None:
        return []
    person = []
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            person.append(ent.text)
    return person


def awards_in_hashtag(tweets):
    """
    Given a list of tweets, extract the awards from the hashtags.
    :param tweets: list of tweet data.
    :return: list of awards.
    """
    awards = set()
    pattern = r"best\w+"
    for tweet in tweets:
        for hashtag in tweet.hashtags:
            match = re.match(pattern, hashtag, re.I)
            if match:
                awards.add(match.group())
    awards = list(awards)
    awards.sort(key=len, reverse=True)
    res = awards[:3]  # Top 3 longest awards
    return [' '.join(wordninja.split(r)).lower() for r in res]


def main():
    # path = input("Enter the path of the dataset: ")
    path = 'gg2013.json'
    dataset = load_tweets(path)
    awards = awards_in_hashtag(dataset)  # Placeholder awards list
    award_nominees = {}

    for tweet in dataset:
        if tweet.text is None:
            continue
        text = tweet.text
        text = process_text(text)

        matches = re.findall(r"(.+) (win|receive|get) (.+)", text)

        if matches:
            threshold = 20  # Threshold
            score = 0
            award_tmp = ''
            for a in awards:
                tmp_score = fuzz.ratio(matches[0][2], a)
                if tmp_score > score:
                    score = tmp_score
                    award_tmp = a
            if award_tmp and score > threshold:
                nominees = find_nominees(matches[0][0])
                if nominees:  # Person exists & award exists
                    if award_tmp in award_nominees:
                        nominees = set(nominees)
                        award_nominees[award_tmp].union(nominees)
                    else:
                        print('Found new award:', award_tmp)
                        award_nominees[award_tmp] = set(nominees)
        # else:
        #     persons = find_person(text)
        #     if persons:  # No pattern but person exists
        #         continue

    print("Awards and Nominees:")
    for k, v in award_nominees.items():
        print(k, v)


if __name__ == "__main__":
    main()
    # tweets = load_tweets('gg2013.json')
    # awards = awards_in_hashtag(tweets)
    # print(awards)
    # print(match_films_with_imdb('Godfather'))


