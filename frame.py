from data import load_data
from tweet import Tweet
import spacy
import re
from fuzzywuzzy import process
import time
import preprocess
import json
from collections import defaultdict
from spacy.matcher import Matcher
from imdb import Cinemagoer
from concurrent.futures import ProcessPoolExecutor
from clustering import cluster_by_timestamp, cluster_tweets_kmeans
from datetime import datetime
from bisect import bisect_left, bisect_right
import os

# Load the spaCy model outside of the function if possible
def extract_names(text, nlp_model): 
    """
    Extracts and prints the names (PERSON entities) found in the given text.

    Parameters:
    text (str): The input sentence or text to analyze.

    Returns:
    List of extracted names.
    """
    # Process the text using spaCy NLP pipeline
    doc = nlp_model(text)
    names = []
    # Extract and print entities labeled as PERSON
    names = [
    ent.text for ent in doc.ents 
    if ent.label_ == "PERSON" 
    and len(ent.text.split()) < 3 
    and not ent.text.endswith("'s")
]
    return names

def merge_name_counts(name_dict, threshold=90):
    """
    Merges counts from first names and full names.
    
    Parameters:
    name_dict (dict): A dictionary with names as keys and counts as values.
    threshold (int): The similarity threshold for merging names.

    Returns:
    dict: A new dictionary with merged names and their counts.
    """
    merged_dict = {}

    # Process each name in the original dictionary.
    for name, count in name_dict.items():
        # If there are already names in merged_dict, try to find the closest match.
        if merged_dict:
            closest_match, score = process.extractOne(name, merged_dict.keys())
            if score >= threshold:
                if len(closest_match) >= len(name):
                    merged_dict[closest_match] += count
                else:
                    # Transfer the count to full name.
                    merged_dict[name] = merged_dict.pop(closest_match) + count
            else:
                # Otherwise, add the new name to the merged dictionary
                merged_dict[name] = count
        else:
            # If merged_dict is empty, add one element into it.
            merged_dict[name] = count

    return merged_dict
def find_host_candidate(tweets: list[Tweet], top_num_show = None) -> dict:
    """
    find possible host candidate who can potentially be a ceremony host
    
    Parameters:
    tweets: A list contains Tweet data structure.
    top_num_show: show top n numbers of candidates instead of the whole list.

    returns:
    A dictionary that ranks the possible host possible candidates from high to low based
    on appearance time.
    """

    # pattern that contains the word host.
    pattern = r"\bhost(s|ed|ing)?\b"

    # Load the small English language model
    nlp = spacy.load("en_core_web_sm")
    # dictionary of possible host candidate
    host_candidate = {}
    for tweet in tweets:
        text = tweet.text
        # if there is host keyword and there is a person name in the sentence,
        # add it to the candidate dictionary.
        if bool(re.search(pattern, text, re.IGNORECASE)):
            name_list = extract_names(text, nlp)
            for name in name_list:
                if name not in host_candidate:
                    host_candidate[name] = 1
                else:
                    host_candidate[name] += 1
    merged_host_candidate = merge_name_counts(host_candidate)
    #add a top numbers option, which is, show only specific numbers of top possible candidate
    if top_num_show:
           sorted_host_candidate = clean_dict_keys(dict(
        sorted(merged_host_candidate.items(), key=lambda item: item[1], reverse=True)[:top_num_show]
        ))
    else:
        sorted_host_candidate = clean_dict_keys(dict(
            sorted(merged_host_candidate.items(), key=lambda item: item[1], reverse=True)
            ))
        
    return sorted_host_candidate
def clean_key(key):
    """
    Cleans the key 's and other strange sign.
    """
    cleaned_key = re.sub(r"\Ws|\W+", ' ', key).strip()
    return cleaned_key

def clean_dict_keys(input_dict):
    """
    Cleans the keys of the given dictionary
    """
    cleaned_dict = {}

    for key, value in input_dict.items():
        # Clean the key
        cleaned_key = clean_key(key)

        # Merge the values if the cleaned key already exists, otherwise add it
        if cleaned_key in cleaned_dict:
            cleaned_dict[cleaned_key] += value
        else:
            cleaned_dict[cleaned_key] = value

    return cleaned_dict


# print(find_host_candidate(All_Tweets, 5))

def find_awards(all_tweets: list) -> dict:
    """
    Find possible awards among all tweets.

    Parameters:
        all_tweets (list): The dataset of all the tweets.
    
    Returns:
        dict: A dictionary of detected awards and their counts.
    """
    nlp = spacy.load("en_core_web_sm")

    # Initialize the Matcher
    matcher = Matcher(nlp.vocab)
    # Define award patterns
    award_patterns = [
    [
        {"IS_TITLE": True, "LOWER": "best"},
        {"IS_TITLE": True, "POS": "PROPN"},
        {"TEXT": "-", "OP": "?"},
        {"IS_TITLE": True, "POS": {"IN": ["PROPN", "NOUN", "ADJ"]}, "OP": "?"}
    ],
    [
        {"IS_TITLE": True, "LOWER": "best"},
        {"IS_TITLE": True, "LOWER": "performance"},
        {"LOWER": "by"},
        {"IS_TITLE": True, "LOWER": {"IN": ["actor", "actress"]}},
        {"LOWER": "in"},
        {"POS": {"IN": ["PROPN", "VERB", "NOUN"]}, "OP": "+"}
    ]
]

    # Add the patterns to the matcher
    matcher.add("AWARD", award_patterns)

    # Use defaultdict to store awards and winners for better performance
    detected_awards = defaultdict(lambda: {
        "count": 0,
        "winners": defaultdict(int),
        "start_timestamp": None,
        "end_timestamp": None
    })

    # Use nlp.pipe() for faster batch processing
    for tweet in all_tweets:
        doc = nlp(tweet.text)
        matches = matcher(doc)
        
        # Extract possible winners only once per tweet
        possible_winners = extract_names(doc.text, nlp)
        
        # Convert matches to spans
        spans = [doc[start:end] for match_id, start, end in matches]
        filtered_spans = filter_longest_spans(spans)

        for span in filtered_spans:
            award = span.text.strip()
            if len(award.split(" ")) > 3:
                award_data = detected_awards[award]
                
                # Update count
                award_data["count"] += 1

                # Update timestamps
                if not award_data["start_timestamp"] or tweet.timestamp < award_data["start_timestamp"]:
                    award_data["start_timestamp"] = tweet.timestamp
                if not award_data["end_timestamp"] or tweet.timestamp > award_data["end_timestamp"]:
                    award_data["end_timestamp"] = tweet.timestamp

                # Filter winners to avoid single-word names
                possible_winners_filter = [winner for winner in possible_winners if len(winner.split(" ")) > 1]
                
                if possible_winners_filter:
                    for winner in possible_winners_filter:
                        award_data["winners"][winner] += 1
                else:
                    # If no valid person names found, try to identify movies
                    possible_movie = find_movie_from_text(award)
                    if possible_movie:
                        award_data["winners"][possible_movie] += 1

    # Sort detected awards by count
    sorted_detected_awards = sorted(detected_awards.items(), key=lambda item: item[1]["count"], reverse=True)
    # discard awards with count less than 2
    sorted_detected_awards = [award for award in sorted_detected_awards if award[1]["count"] > 1]
    # Convert to regular dict and format timestamps as readable dates
    sorted_detected_awards = {
        award: {
            **data,
            "start_timestamp": data["start_timestamp"] ,
            "end_timestamp": data["end_timestamp"],
            "winners": clean_dict_keys(data["winners"])
        }
        for award, data in sorted_detected_awards
    }

    return sorted_detected_awards

def find_movie_from_text(text):
    """
    Tries to find movie title from the given text using regex-based splitters.
    """
    # Define regex-based patterns to extract movie titles
    splitters_after = [r":", r"-", r"goes to", r"winner is"]
    splitters_before = [r"wins", r"win"]

    for splitter in splitters_after:
        if re.search(splitter, text):
            parts = re.split(splitter, text, maxsplit=1)
            if len(parts) > 1:
                return parts[1].strip()
    
    for splitter in splitters_before:
        if re.search(splitter, text):
            parts = re.split(splitter, text, maxsplit=1)
            if len(parts) > 1:
                return parts[0].strip()
    
    return None
def filter_longest_spans(spans):
    """Filter overlapping spans to keep only the longest ones."""
    # Sort spans by start index, and if equal, by end index descending
    sorted_spans = sorted(spans, key=lambda span: (span.start, -span.end))
    longest_spans = []
    last_end = -1

    for span in sorted_spans:
        if span.start >= last_end:
            longest_spans.append(span)
            last_end = span.end

    return longest_spans
def test_dependency(text):
    ia = Cinemagoer()
    random_tweet = Tweet()
    random_tweet.text = text
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    for token in doc:
        print(f"Word: {token.text}, POS: {token.pos_}, Tag: {token.tag_}")
        if is_movie(token.text, ia):
            print(token.text, "is moive")
    print([(ent.text, ent.label_)for ent in doc.ents])
    rewards = []
    rewards.append(random_tweet)
    print(find_awards(rewards))

def is_movie(title, imdb):
    """
    Checks if the given title is a movie in IMDb.

    Parameters:
    title (str): The title to check.

    Returns:
    bool: True if the title is a movie, False otherwise.
    """
    
    search_results = imdb.search_movie(title)
    
    # Check if the search results contain a movie that matches the title
    for result in search_results:
        if result['title'].lower() == title.lower():
            return True
    
    return False

def find_nominees(tweets, detected_awards):
    """
    Map nominees to their respective awards.

    Parameters:
        tweets (list): List of tweet objects.
        detected_awards (dict): dictionary of detected awards and their counts and winners.
        
    Returns:
        dict: A dictionary with awards as keys and lists of nominees as values.
    """
    nlp = spacy.load("en_core_web_sm")
    matcher = Matcher(nlp.vocab)
    
    # Patterns to capture nominee phrases
    nominee_patterns = [
        [{"IS_TITLE": True}, {"LOWER": "nominated"}, {"LOWER": "for"}, {"IS_TITLE": True, "OP": "+"}],   # "X nominated for Y"
        [{"IS_TITLE": True}, {"LOWER": "nominee"}, {"IS_PUNCT": True, "OP": "?"}, {"IS_TITLE": True, "OP": "+"}],  # "X nominee: Y"
        [{"IS_TITLE": True, "OP": "+"}, {"LOWER": "up"}, {"LOWER": "for"}, {"IS_TITLE": True, "OP": "+"}],  # "X up for Y"
    ]

    matcher.add("NOMINEE_AWARD", nominee_patterns)

    # Initialize a dictionary to store award-nominee mappings
    award_nominee_map = {award: [] for award in detected_awards.keys()}
    for award in detected_awards.keys():
        winners = detected_awards[award]["winners"]
        if winners:
            for winner in winners.keys():
                award_nominee_map[award].append(winner)

    # Process each tweet to find nominee-award relationships
    for award in detected_awards.keys():
        # filter tweets by timestamp, assuming tweets were already sorted by timestamp
        filtered_tweets = filter_tweets_by_timestamp(tweets, detected_awards[award]["start_timestamp"], detected_awards[award]["end_timestamp"])
        for tweet in filtered_tweets:
            doc = nlp(tweet.text)
            matches = matcher(doc)
            
            for match_id, start, end in matches:
                span = doc[start:end]
                nominee_text = None
                award_text = None
                
                # Extract entities within a reasonable distance from the pattern span
                for token in span:
                    # Search for a nominee entity (typically a person or film title)
                    if token.ent_type_ in {"PERSON", "ORG", "WORK_OF_ART"}:
                        nominee_text = token.text
                        
                    # Match award names using detected award list
                    for award in detected_awards.keys():
                        if award.lower() in tweet.text.lower():
                            award_text = award
                            break
                    
                # If both nominee and award are found, add nominee to award_nominee_map
                if nominee_text and award_text:
                    award_nominee_map[award_text].append(nominee_text)
                


    # Remove duplicates and return the map
    for award in award_nominee_map:
        award_nominee_map[award] = list(set(award_nominee_map[award]))  # Eliminate duplicates

    return award_nominee_map

def find_presenters(tweets, detected_awards):
    """
    Map presenters to their respective awards.

    Parameters:
        tweets (list): List of tweet objects.
        detected_awards (list): List of detected award names.
        
    Returns:
        dict: A dictionary with presenters as keys and lists of awards as values.
    """
    nlp = spacy.load("en_core_web_sm")
    matcher = Matcher(nlp.vocab)
    
    # Patterns to capture presenter phrases
    presenter_patterns = [
        [{"IS_TITLE": True}, {"LOWER": "presents"}, {"IS_TITLE": True, "OP": "+"}],   # "X presents Y"
        [{"IS_TITLE": True}, {"LOWER": "announces"}, {"IS_TITLE": True, "OP": "+"}],  # "X announces Y"
        [{"IS_TITLE": True}, {"LOWER": "to"}, {"LOWER": "present"}, {"IS_TITLE": True, "OP": "+"}],  # "X to present Y"
    ]

    matcher.add("PRESENTER_AWARD", presenter_patterns)

    # Initialize a dictionary to store presenter-award mappings
    award_presenter_map = {}

    # Process each tweet to find presenter-award relationships
    for award in detected_awards:
        # filter tweets by timestamp, assuming tweets were already sorted by timestamp
        filtered_tweets = filter_tweets_by_timestamp(tweets, detected_awards[award]["start_timestamp"], detected_awards[award]["end_timestamp"])
        for tweet in filtered_tweets:
            doc = nlp(tweet.text)
            matches = matcher(doc)
            
            for match_id, start, end in matches:
                span = doc[start:end]
                presenter_text = None
                award_text = None
                
                # Extract entities within a reasonable distance from the pattern span
                for token in span:
                    # Search for a presenter entity (typically a person)
                    if token.ent_type_ == "PERSON":
                        presenter_text = token.text
                        
                    # Match award names using detected award list
                    for award in detected_awards:
                        if award.lower() in tweet.text.lower():
                            award_text = award
                            break
                
                # If both presenter and award are found, add presenter to award_presenter_map
                if presenter_text and award_text:
                    if presenter_text not in award_presenter_map:
                        award_presenter_map[presenter_text] = []
                    award_presenter_map[presenter_text].append(award_text)

    # Remove duplicates from award lists
    for presenter in award_presenter_map:
        award_presenter_map[presenter] = list(set(award_presenter_map[presenter]))  # Eliminate duplicates

    return award_presenter_map

def filter_tweets_by_timestamp(tweets, start_timestamp, end_timestamp):
    """
    Filter tweets based on a timestamp range using binary search for efficiency.

    Parameters:
        tweets (list): A list of Tweet objects sorted by timestamp.
        start_timestamp (int): The start timestamp of the range.
        end_timestamp (int): The end timestamp of the range.

    Returns:
        list: A list of tweets within the specified timestamp range.
    """
    # Extract the list of timestamps
    timestamps = [tweet.timestamp for tweet in tweets]

    # Use binary search to find the range indices
    start_index = bisect_left(timestamps, start_timestamp)
    end_index = bisect_right(timestamps, end_timestamp)

    # Slice the tweets list to get only those within the range
    return tweets[start_index:end_index]

def process_cluster(timestamp, cluster):
    awards = find_awards(cluster)
    nominees = find_nominees(cluster, awards)
    presenters = find_presenters(cluster, awards)
    return timestamp, awards, nominees, presenters

def get_winner(award):
    winners = award["winners"]
    if winners:
        return max(winners, key=winners.get)
    return None

def print_result(host_candidates, awards, nominees, presenters):
    # choose the top 3 host candidates
    print("Hosts: ", list(host_candidates.keys())[:3])
    
    for awardname, award in awards.items():
        print(f'Award: {awardname}')
        print("Presenters: ", presenters[awardname] if awardname in presenters else None)
        print("Nominees: ", nominees[awardname] if awardname in nominees else None)
        print("Winner: ", get_winner(award))
        print("\n")
    
def save_json(host_candidates, awards, nominees, presenters, filename):
    # remove file if it already exists
    if os.path.exists(filename):
        os.remove(filename)

    with open(filename, "w") as file:
        json.dump({
            "Hosts": list(host_candidates.keys())[:3],
            "Award data":[
                {
                    "Award": awardname,
                    "Presenters": presenters[awardname] if awardname in presenters else None,
                    "Nominees": nominees[awardname] if awardname in nominees else None,
                    "Winner": get_winner(award)
                } for awardname, award in awards.items()
            ]
        }, file, indent=4)
    print(f"Results saved to {filename}")

if __name__ == "__main__":
    time1 = time.time()
    All_Tweets = preprocess.preprocess("gg2013.json")
    #clustered_tweets = cluster_by_timestamp(All_Tweets)
    print("Clustering tweets...")
    clustered_tweets = cluster_tweets_kmeans(All_Tweets, k=32)

    print("Finding host candidates...")
    host_candidates = find_host_candidate(All_Tweets)

    awards_result = {}
    nominees_result = {}
    presenters_result = {}

    print("Processing clusters...")
    with ProcessPoolExecutor() as executor:
        future_results = [executor.submit(process_cluster, timestamp, cluster) for timestamp, cluster in clustered_tweets.items()]
        for future in future_results:
            timestamp, awards, nominees, presenters = future.result()
            print(awards)
            print(nominees)
            print(presenters)
            #merge dictionaries into results
            awards_result.update(awards)
            nominees_result.update(nominees)
            presenters_result.update(presenters)
    
    print("Printing results...")
    print_result(host_candidates, awards_result, nominees_result, presenters_result)
    save_json(host_candidates, awards_result, nominees_result, presenters_result, "result.json")
    time2 = time.time()
    print(time2 - time1, "s")
    