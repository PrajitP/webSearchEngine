import sys
import os
import pickle
import nltk
import re
from bs4 import BeautifulSoup
from collections import defaultdict
sys.path.append('externalLib')
from crawler import Crawler

def collect_data(outDir):
    crawler = Crawler(outDir = outDir)
    crawler.start(
        domain = 'https://en.wikipedia.org',                    # Explore pages with-in this domain
        seedLink = 'https://en.wikipedia.org/wiki/Database',    # Start exploring from this page
        dumpInterval = 10,                                      # Dump explored pages after every '10' exploration
        maxExplore = 120) 

tokenIndex = defaultdict(list)
def index_document(docName, docData, docIndex):
    docIndexMapping[docIndex] = docName    
    # Reference: https://stackoverflow.com/questions/1936466/beautifulsoup-grab-visible-webpage-text
    soup = BeautifulSoup(docData, 'html.parser')
    [tag.extract() for tag in soup(['style', 'script', '[document]', 'head', 'title'])]
    visible_text = soup.getText()
    tokens = nltk.word_tokenize(visible_text)
    tokenFreq = {}
    for token in tokens:
        token = token.lower()
        if not re.search(r'.*[a-z].*', token):
            continue
        if token in tokenFreq:
            tokenFreq[token] += 1
        else:
            tokenFreq[token] = 1
    for token, freq in tokenFreq.items():
        tokenIndex[token].append(str(docIndex) + "@" + str(freq))

def index_data(inDir, outDir):
    files = []
    for (dirpath, dirnames, filenames) in os.walk(inDir):
        files.extend(filenames)
        break
    docIndex = 1
    for file in files:
        with open(os.path.join(inDir, file), 'rb') as fileHandle:
            data = pickle.load(fileHandle)
        for key,value in data.items():
            index_document(key, value, docIndex)
            docIndex += 1
    #print(docIndexMapping)

# Get the data
crawlerOutdir = 'TMP/crawlOut'
if not os.path.exists(crawlerOutdir):
    collect_data(crawlerOutdir)
else:
    print("Data already available at: " + crawlerOutdir)

# Index data
docIndexMapping = {}
index_data(crawlerOutdir, 'TMP/indexOut')
print(tokenIndex)
