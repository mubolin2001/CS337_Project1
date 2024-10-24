"""
Data structure for storing tweet information.
"""


class Tweet:
    id: int
    text: str
    user: str
    timestamp: str
    hashtags: list

    def __init__(self, id=None, text=None, user=None, timestamp=None, hashtags=None):
        self.id = id
        self.text = text
        self.user = user
        self.timestamp = timestamp
        self.hashtags = hashtags
