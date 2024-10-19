from tweet import Tweet
def find_host_candidate(tweets):
    """
    find possible host candidate who can potentially be a ceremony host
    
    Parameters:
    tweets: A list contains Tweet data structure.

    returns:
    A dictionary that ranks the possible host possible candidates from high to low based
    on appearance time.
    """
    