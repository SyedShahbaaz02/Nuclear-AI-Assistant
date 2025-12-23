import re, html
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer


class Common():
    # Function to pre-process or clean string
    def preprocess_text(text: str, pattern: str, clean_text: bool) -> str:

        # Convert characters back to original, like &apos;
        text = html.unescape(text)

        # Search and extract for the pattern
        match = re.search(pattern, text)
        text = match.group(1) if match else text

        if clean_text:

            # Remove links
            text = re.sub(r"http\S+", "", text)

            # Remove special chars
            text = re.sub("[^A-Za-z0-9]+", " ", text)

            # Remove single characters (excluding spaces)
            text = re.sub(r'\b\w\b', '', text)

            # Remove extra spaces caused by removal
            text = re.sub(r'\s+', ' ', text).strip()

            # Tokenize for further cleaning
            tokens = nltk.word_tokenize(text)

            # Remove stopwords
            tokens = [w for w in tokens if not w.lower() in stopwords.words("english")]

            # Lemmatization - Convert verbs to basic form
            wnl = WordNetLemmatizer()
            tokens = [wnl.lemmatize(w, pos="v") for w in tokens]

            text = " ".join(tokens)
            text = text.lower().strip()

        return text
