import sys
import os
import pickle
import re
import math
from bs4 import BeautifulSoup
from collections import defaultdict
sys.path.append('externalLib')
from crawler import Crawler
import nltk
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer

def collect_data(outDir):
    crawler = Crawler(outDir = outDir)
    crawler.start(
        domain = 'https://en.wikipedia.org',                    # Explore pages with-in this domain
        seedLink = 'https://en.wikipedia.org/wiki/Database',    # Start exploring from this page
        dumpInterval = 10,                                      # Dump explored pages after every '10' exploration
        maxExplore = 120) 

def dumpStructure(fileName, content):
    with open(fileName, 'wb') as fileHandle:
        pickle.dump(content, fileHandle, protocol=pickle.HIGHEST_PROTOCOL)

stemmer = PorterStemmer()
stop_words = set(stopwords.words('english'))
def index_document(document):
    # Create BeautifulSoup object from html text, and ignore/remove the non-ASCII 
    soup = BeautifulSoup(document.encode("ascii", errors='ignore'), 'html.parser')
    # Remove non-visible tags [Reference: https://stackoverflow.com/questions/1936466/beautifulsoup-grab-visible-webpage-text]
    [tag.extract() for tag in soup(['style', 'script', '[document]', 'head', 'title'])]
    # Get visible text from html document
    visible_text = soup.getText()
    # Tokenize
    tokens = nltk.word_tokenize(visible_text)

    # To capture occurrence of 'token/term' in a 'document'
    tokenFreq = {}
    for token in tokens:
        # Convert all character to lower case
        token = token.lower()
        # Ignore token which does not have alphabet
        if not re.search(r'.*[a-z].*', token):
            continue
        # Apply stemming
        token = stemmer.stem(token)
        # Ignore stopword
        if token in stop_words:
            continue
        # Count frequency
        if token in tokenFreq:
            tokenFreq[token] += 1
        else:
            tokenFreq[token] = 1
    return (tokenFreq, len(tokens))

def index_data(inDir, outDir):
    docLink_to_docId_map = {}
    token_to_docId_map   = defaultdict(list)
    # Use 'document id' instead of 'document link' as 'id' is shorter and will take less memory then 'link'
    docId = 1
    # Get list of data files from input directory
    dataFiles = [dataFile for dataFile in os.listdir(inDir) if os.path.isfile(os.path.join(inDir, dataFile))]
    # Read the data file
    for dataFile in dataFiles:
        with open(os.path.join(inDir, dataFile), 'rb') as fileHandle:
            data = pickle.load(fileHandle)
        # Build the 'term document index'
        for docLink,docData in data.items():
            # Map 'document id' to 'document link'
            docLink_to_docId_map[docId] = docLink   
            # Index document
            tokenFreq, totalTokens = index_document(docData)
            # Update all terms/tokens belonging to document
            for token, freq in tokenFreq.items():
                # Calculate 'Term Frequency', which states importance of 'Term' in 'Document'
                tokenWeight = (1 + math.log10(freq)) if freq else 0
                token_to_docId_map[token].append(format(tokenWeight, '.8f') + "@" + str(docId))
            # Increment 'document id' for next iteration
            docId += 1
    # Store the output
    if not os.path.exists(outDir):
        os.makedirs(outDir)
    dumpStructure(os.path.join(outDir, 'docLink_to_docId_map'), docLink_to_docId_map)
    dumpStructure(os.path.join(outDir, 'token_to_docId_map'), token_to_docId_map)

# Get the data
crawlerOutdir = 'TMP/crawlOut'
if not os.path.exists(crawlerOutdir):
    collect_data(crawlerOutdir)
else:
    print("Data already available at: " + crawlerOutdir)

# Index data
indexOutdir = 'TMP/indexOut'
index_data(crawlerOutdir, indexOutdir)
#print(tokenIndex)
