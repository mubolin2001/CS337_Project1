from data import load_data
from tweet import Tweet
import spacy
import re
from fuzzywuzzy import process
import time
# import preprocess
import json
from spacy.matcher import Matcher
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

 
import spacy
from spacy.matcher import Matcher

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
        # Pattern: "Best" + optional category + optional hyphen + medium/genre
        [
            { "IS_TITLE": True, "LOWER": "best"},
            {"IS_TITLE": True, "POS": "PROPN", "OP": "+"},  
            {"TEXT": "-", "OP": "?"},  # Optional hyphen
            {"IS_TITLE": True, "POS": {"IN": ["PROPN", "NOUN", "ADJ"]}, "OP": "?"},
             {"IS_TITLE": True, "POS": {"IN": ["PROPN", "NOUN", "ADJ"]}, "OP": "?"},
            {"LOWER": "or", "OP": "?"},
            {"IS_TITLE": True, "POS": {"IN": ["PROPN", "NOUN", "ADJ"]}, "OP": "?"}
        ],
        # Pattern: "Best Performance by Actor/Actress" + "in a ..."
        [
            {"IS_TITLE": True, "LOWER": "best"},
            {"IS_TITLE": True,"LOWER": "performance"},
            {"LOWER": "by"},
            {"LOWER": {"IN": ["a", "an"]}, "OP": "?"},
            {"IS_TITLE": True,"LOWER": {"IN": ["actor", "actress"]}},
            {"LOWER": "in"},
            {"LOWER": "a"},
            {"POS": {"IN": ["PROPN", "VERB", "NOUN"]}, "OP": "+"},  #in a + " VERB" + "PREPN"
            {"LOWER": "in", "OP": "?"},
            {"LOWER": "a", "OP": "?"},
            {"POS": {"IN": ["PROPN", "VERB", "NOUN"]}, "OP": "?"},
            {"POS": {"IN": ["PROPN", "VERB", "NOUN"]}, "OP": "?"},
            {"TEXT": "-", "OP": "?"},  # Optional hyphen
            {"POS": "PROPN", "OP": "?"}, 
             {"LOWER": "or", "OP": "?"},
             {"POS": "PROPN", "OP": "?"}
        ],
    ]

    # Add the patterns to the matcher
    matcher.add("AWARD", award_patterns)

    # Store detected awards in a dictionary
    detected_awards = {}

    # Use nlp.pipe() for faster batch processing
    for doc in nlp.pipe((tweet.text for tweet in all_tweets), batch_size=50):
        matches = matcher(doc)

        # Convert matches to spans
        spans = [doc[start:end] for match_id, start, end in matches]

        # Filter to keep only the longest non-overlapping matches
        filtered_spans = filter_longest_spans(spans)

        # Store the matches in the dictionary
        for span in filtered_spans:
            award = span.text
            if award in detected_awards:
                detected_awards[award] += 1
            else:
                detected_awards[award] = 1
            
            

    sorted_detected_awards = sorted(detected_awards.items(), key = lambda item: item[1], reverse=True)

    return sorted_detected_awards

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
print()
All_Tweets = load_data("gg2013.json")
def test_dependency(text):
    random_tweet = Tweet()
    random_tweet.text = text
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    for token in doc:
        print(f"Word: {token.text}, POS: {token.pos_}, Tag: {token.tag_}")
    print([(ent.text, ent.label_)for ent in doc.ents])
    rewards = []
    rewards.append(random_tweet)
    print(find_awards(rewards))
# test_dependency(
    
# )
time1 = time.time()
print(find_awards(All_Tweets))
time2 = time.time()
print(time2 - time1, "s")
# with open("gg2013answers.json", "r") as file:
#     data = json.load(file)
#     for award in data['award_data']:
#         print(award)
#         print()
    