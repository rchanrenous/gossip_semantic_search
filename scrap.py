from bs4 import BeautifulSoup
from typing import List
from urllib.request import Request, urlopen
import urllib.parse as urlparse
from urllib.parse import urlencode
#from dotenv import load_dotenv
#from os import getenv

def remove_tags(s: str) -> str:
    '''
    Parse content retrieved from paragraph tag in an HTML document.
    Removes tags from paragraph content. Keeps the content inside the nested tags.
    
    Parameters:
        s: paragraph tag content; the string is expected to have valid HTML syntax and the "<" and ">" symbols are not used in the text

    Returns:
        res: the parsed string content of the paragraph tag
    '''

    res = ""
    i = 0
    j = 0
    size = len(s)
    L = []
    open_tag = False
    while j < len(s):
        if s[j] == "<":
            open_tag = True
            if i != j:
                L.append(s[i:j])
            j += 1
            while j < size and s[j] != ">":
                j += 1
            if j < size and s[j] == ">":
                open_tag = False
                j += 1
                i = j
        else:
            j += 1
    if i != j:
        L.append(s[i:j])
    res = " ".join(L)
    if open_tag == True:
        print("Invalid HTML syntax.")
    return res

class ArticleScrapper:
    '''
    Scrap article text.

    Attributes:
        paragraph_tag_name: tag name of the paragraph element that contains the text
        parser: webpage parser
    '''

    def __init__(self, paragraph_tag_name: str="p", parser: str="lxml"):
        '''
        Initialize attributes.
        '''

        self.paragraph_tag_name = paragraph_tag_name
        self.parser = parser


    def scrap(self, url: str) -> str:
        '''
        Get the text content from the article located at the URL.

        Parameters:
            url: url of the article

        Returns:
            article: the article text
        '''

        with urlopen(url) as response:
            soup = BeautifulSoup(response, self.parser)
            L = []
            empty = True
            for paragraph in soup.find_all(self.paragraph_tag_name):
                L.append(paragraph.text)
            article = " ".join(L)
        return article


    def scrap_date(self, url: str) -> str:
        '''
        Return the publishing date of an article.

        Parameters:
            url: article url

        Returns:
            time: string containing the article publishing date
        '''

        with urlopen(url) as response:
            soup = BeautifulSoup(response, self.parser)
            time = soup.find("time").text
        return time


    def scrap_linkup(self, params: dict, headers: dict, url: str="https://api.linkup.so/v1/content") -> str:
        '''
        Scrap article content using Linkup's API.

        Parameters:
            params: dictionary containing the query
            headers: dictionary containing the API key
            url: API base URL

        Returns:
            Raw API response for the input article (for now)
        '''
        
        url_parts = list(urlparse.urlparse(url))
        query = urlparse.parse_qs(url_parts[4])
        query.update(params)
        url_parts[4] = urlencode(query)
        url = urlparse.urlunparse(url_parts)
        req = Request(url, headers=headers)
        response = urlopen(req)
        # needs parsing
        return (response.read().decode(response.headers.get_content_charset()))       


def main():
    scrapper = ArticleScrapper(paragraph_tag_name="p")
    url_public = "https://www.public.fr/une-etude-revele-la-couleur-des-yeux-des-personnes-les-plus-intelligentes-mythe-ou-realite"
    url_vsd = "https://vsd.fr/73030-nous-on-savait-la-verite-kendji-girac-evoque-avec-emotion-sa-relation-actuelle-avec-sa-femme-soraya/"
    article = scrapper.scrap(url=url_public)
    date = scrapper.scrap_date(url=url_public)
    print(article, date)
    article = scrapper.scrap(url=url_vsd)
    date = scrapper.scrap_date(url=url_vsd)
    print(article, date)

    '''
    # test Linkup API
    load_dotenv()
    LINKUP_API_KEY = getenv("LINKUP_API_KEY")
    print("Number of words:", len(article.split(" ")))
    url = "https://api.linkup.so/v1/content"
    #payload = {"url": "https://vsd.fr/22837-recensement-etes-vous-fils-de-resistant/"}
    #payload = {"url": "https://www.public.fr/une-etude-revele-la-couleur-des-yeux-des-personnes-les-plus-intelligentes-mythe-ou-realite"}
    payload = {"url": "https://www.thebridgechronicle.com/news/capgemini-employees-walk-together-in-celebration-of-indias-independence"}
    headers = {"Authorization": f"Bearer {LINKUP_API_KEY}"}
    article = scrapper.scrap_linkup(url=url, params=payload, headers=headers)
    print(article)
    '''

if __name__ == "__main__":
    main()