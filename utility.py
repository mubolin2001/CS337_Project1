from nltk.corpus import stopwords
import nltk

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

# Function to check if a word is a stopword
def is_stopword(word):
    stop_words = set(stopwords.words('english'))
    return word.lower() in stop_words
