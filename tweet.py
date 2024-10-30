"""
Data structure for storing tweet information.
"""
from datetime import datetime


class Tweet:
    def __init__(self, id=None, text=None, user=None, timestamp=None, hashtags=None):
        self.id = id
        self.text = text
        self.user = user
        self.timestamp = timestamp
        self.hashtags = hashtags
    
    def __str__(self):
        return f"Tweet: {self.text} by {self.user} at {datetime.fromtimestamp(self.timestamp/1000).strftime('%Y-%m-%d %H:%M:%S')} with hashtags {self.hashtags}"