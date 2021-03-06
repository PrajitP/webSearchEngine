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
def index_string(text):
    # Tokenize
    tokens = nltk.word_tokenize(text)
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

def index_document(document):
    # Create BeautifulSoup object from html text, and ignore/remove the non-ASCII 
    soup = BeautifulSoup(document.encode("ascii", errors='ignore'), 'html.parser')
    # Remove non-visible tags [Reference: https://stackoverflow.com/questions/1936466/beautifulsoup-grab-visible-webpage-text]
    [tag.extract() for tag in soup(['style', 'script', '[document]', 'head', 'title'])]
    # Get visible text from html document
    visible_text = soup.getText()
    return index_string(visible_text)

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
            # Index document, i.e. get list of tokens in document
            tokenFreq, totalTokens = index_document(docData)
            # Create token to document mapping
            for token, tokenDocFreq in tokenFreq.items():
                # Calculate 'Term/token Frequency', which states importance of 'Token' in 'Document'
                tokenDocScore = (1 + math.log10(tokenDocFreq)) if tokenDocFreq else 0
                token_to_docId_map[token].append((docId, tokenDocScore))
            # Increment 'document id' for next iteration
            docId += 1
    # Store the output
    if not os.path.exists(outDir):
        os.makedirs(outDir)
    dumpStructure(os.path.join(outDir, 'docLink_to_docId_map'), docLink_to_docId_map)
    dumpStructure(os.path.join(outDir, 'token_to_docId_map'), token_to_docId_map)

def loadStructure(fileName):
    with open(fileName, 'rb') as fileHandle:
        data = pickle.load(fileHandle)
    return data

def get_relevant_documents(inDir, query):
    token_to_docId_map = loadStructure(os.path.join(inDir, 'token_to_docId_map'))
    docLink_to_docId_map = loadStructure(os.path.join(inDir, 'docLink_to_docId_map'))
    tokenFreq, totalTokens = index_string(query)
    documentRanks = {}
    # Get scores for all relevant documents using relevant tokens from search query
    for token, tokenDocFreq in tokenFreq.items():
        documentsForToken = token_to_docId_map[token]
        for (docId, tokenDocScore) in documentsForToken:
            # Calculate tf-idf score, properties of this score are:
            # - Increases with number of occurrences with in a document
            # - Increases with rarity of term across documents
            tokenDocCount = len(documentsForToken)  # Number of documents in which token exists
            totalDocCount = totalDocuments          # Total number of documents
            tfIdfScore = tokenDocScore * math.log10(totalDocCount/tokenDocCount)
            if docId in documentRanks:
                documentRanks[docId] += tfIdfScore
            else:
                documentRanks[docId] = tfIdfScore
    # Sort the documents by score
    sortedDocumentRanks = sorted(documentRanks, key=documentRanks.get, reverse=True)
    # Get top 5 document links
    finalDocumentList = []
    for docId in sortedDocumentRanks[:5]:
        finalDocumentList.append(docLink_to_docId_map[docId])
    # Return top 5 document links
    return finalDocumentList

# Get the data
crawlerOutdir = 'TMP/crawlOut'
if not os.path.exists(crawlerOutdir):
    collect_data(crawlerOutdir)
else:
    print("Data already available at: " + crawlerOutdir)

# Index data
indexOutdir = 'TMP/indexOut'
if not os.path.exists(indexOutdir):
    index_data(crawlerOutdir, indexOutdir)
else:
    print("Index already available at: " + indexOutdir)

totalDocuments = 100
documents = get_relevant_documents(indexOutdir, 'what is sql')
for document in documents:
    print(document)
