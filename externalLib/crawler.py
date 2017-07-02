from bs4 import BeautifulSoup
import os
import pickle
import re
import urllib

class LinkProcessor:
    domain = ''

    def __init__(self, domain):
        self.domain = domain

    def isInternalRelativeLink(self, link):
        reInternalRelLink = re.compile(r"^/")      # Link that starts with '/'
        match = reInternalRelLink.search(link)
        return (True if (match) else False)

    def isInternalAbsoluteLink(self, link):
        reInternalAbsLink = re.compile(r'^' + self.domain)      # Link that starts with 'domain'
        match = reInternalAbsLink.search(link)
        return (True if (match) else False)

    def isDynamicLink(self, link):
        reDynamicLink = re.compile(r"\?")       # Link that has '?'
        match = reDynamicLink.search(link)
        return (True if (match) else False)

    # Example:
    # I/P : /wiki/Wikipedia:Verifiability#Burden_of_evidence
    #           will be converted to
    # O/P : /wiki/Wikipedia:Verifiability
    def sanitizePageSectionInLink(self, link):
        rePageSectionLink = re.compile(r'(#[^#]+)$')
        return rePageSectionLink.sub('', link)

    def getFinalLink(self, link, parentLink):
        # ----------------
        # Sanitize link
        # ----------------
        # Remove the trailing page section if any
        link = self.sanitizePageSectionInLink(link)
        # Convert internal relative link to absolute link
        if self.isInternalRelativeLink(link):
            link = self.domain + link
        # ----------------
        # Filter link
        # ----------------
        # Only explore if link is with in domain
        if not self.isInternalAbsoluteLink(link):
            return None
        # Only explore if link is static
        if self.isDynamicLink(link):
            return None
        # TODO: Remove link with extensions other than 'html'
        return link

class Crawler:
    outDir = 'TMP'

    def __init__(self, outDir):
        self.outDir = outDir
        if not os.path.exists(self.outDir):
            os.makedirs(self.outDir)
        print("Output directory: '%(dir)s'" %{'dir': outDir})

    def dumpCache(self, fileName, content):
        with open(os.path.join(self.outDir, fileName), 'wb') as fileHandle:
            pickle.dump(content, fileHandle, protocol=pickle.HIGHEST_PROTOCOL)

    def start(self, domain, seedLink, linkProcessor = None, dumpInterval = 10, maxExplore = 100):
        if not linkProcessor:
            linkProcessor = LinkProcessor(domain)
        exploredLinkList = {}
        candidateLinks = [seedLink]
        cacheContent = {}
        fileIndex = 0
        for candidateLink in candidateLinks:
            if candidateLink in exploredLinkList:
                continue
            if len(exploredLinkList) >= maxExplore:
                break
            try:
                response = urllib.request.urlopen(candidateLink)
            except urllib.error.HTTPError as e:
                print('The server couldn\'t fulfill the request, Error code: ', e.code)
            except urllib.error.URLError as e:
                print('We failed to reach a server, Reason: ', e.reason)
            responseBody = response.read().decode('utf-8');
            soup = BeautifulSoup(responseBody, 'html.parser')
            exploredLinkList[candidateLink] = 1;
            cacheContent[candidateLink] = responseBody
            print ('.', end = '', flush = True)    # Will print '.' for every page it explore, visual effect to show progress
            if len(cacheContent) >= dumpInterval:
                self.dumpCache(str(fileIndex), cacheContent)
                fileIndex += 1
                cacheContent = {}
            for aTag in soup.find_all('a'):
                link = aTag.get('href')
                if not link:                # skip if 'href' attribute is missing
                    continue
                link = linkProcessor.getFinalLink(link, candidateLink)
                if link:
                    candidateLinks.append(link)
        self.dumpCache(str(fileIndex), cacheContent)
        print("\n%(count)d pages explored" %{'count':len(exploredLinkList)})

if __name__ == '__main__':
    # Explore all the links
    domain = 'https://en.wikipedia.org'
    seedLink = 'https://en.wikipedia.org/wiki/Database'
    crawler = Crawler('tmp')
    crawler.start(domain, seedLink, dumpInterval = 3, maxExplore = 10)

    # Read list of all explored links
    files = []
    for (dirpath, dirnames, filenames) in os.walk('tmp'):
        files.extend(filenames)
        break
    for file in files:
        with open(os.path.join('tmp', file), 'rb') as fileHandle:
            data = pickle.load(fileHandle)
        for key in data.keys():
            print(key)
