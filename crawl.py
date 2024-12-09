from bs4 import BeautifulSoup
from typing import List
from time import time
import csv
from urllib.request import urlopen


def get_links_from_url(url: str,
                        tag_name: str,
                        url_tag_name: str,
                        L_keyword: List[str]=[""],
                        parser: str="xml") -> List[str]:
    '''
    Extract list of URLs from a given URL.

    Args:
        url: URL to get the forward links from.
        keyword: keyword filtering of the forward links URLs; 'None' for no filtering.
        parser: HTML parser.

    Returns:
        L_res: list of forward links from the given URL.
    '''

    L_res = []
    with urlopen(url) as response: 
        soup = BeautifulSoup(response, parser)
        for tag in soup.find_all(tag_name):
            content = tag.find_next(url_tag_name).text
            for keyword in L_keyword:
                if keyword in content:
                    L_res.append(content)
                    break
    return L_res


class ArticlesCrawler():
    '''
    Crawler class to retrieve lists of articles from sitemaps.

    Attributes:
        url: sitemap url
        sitemap_tag_name: tag name of the sitemap files in the main sitemap
        xml_tag_names: tag name of the URLs in the sitemaps
        url_tag_name: tag name of the content in the tags
        L_keyword: list of keyword to filter out the sitemaps; a list with an empty string for no filtering
        parser: URL parser 
    '''

    def __init__(self, 
                url: str, 
                sitemap_tag_name: str="sitemap",
                xml_tag_name: str="url", 
                url_tag_name: str="loc", 
                L_keyword: List[str]=[""], 
                parser: str="xml"):
        '''
        Initializes attributes.
        '''

        self.url = url
        self.sitemap_tag_name = sitemap_tag_name
        self.xml_tag_name = xml_tag_name
        self.url_tag_name = url_tag_name
        self.L_keyword = L_keyword
        self.parser = parser


    def crawl(self) -> List[str]:
        '''
        Performs the articles crawling.

        Returns:
            L_articles: list of the articles
        '''
        
        # get list of sitemaps from main sitemap
        L_sitemap = get_links_from_url(url=self.url,
                                        tag_name=self.sitemap_tag_name, 
                                        url_tag_name=self.url_tag_name, 
                                        L_keyword=self.L_keyword)
        # get list of articles from each sitemap
        L_articles = []
        for sitemap in L_sitemap:
            urls = get_links_from_url(url=sitemap, 
                                        tag_name=self.xml_tag_name, 
                                        url_tag_name=self.url_tag_name)
            L_articles += urls
            print(f"\tsitemap: {sitemap}, {len(urls)} URLs")
        print("Total number of articles:", len(L_articles))
        return L_articles


    def save_articles(self, file_name: str, write_mode: str="w"):
        '''
        Crawl the articles list and saves it to the disk.

        Parameters:
            file_name: path to file where to save the list of articles
            write_mode: writing mode parameter
        '''

        # get the list of articles
        print("Crawling articles from", self.url)
        L_articles = self.crawl()
        # save list of articles in csv format
        print("Saving articles to", file_name)
        f = open(file_name, write_mode)
        writer = csv.writer(f)
        for url in L_articles:
            writer.writerow([url])
        f.close()

def main():
    
    sitemap_keywords = ["/post-sitemap", "/slideshow-sitemap", "/video-sitemap"]
    publicCrawler = ArticlesCrawler(url="https://www.public.fr/sitemap_index.xml",
                                    L_keyword=sitemap_keywords)
    vsdCrawler = ArticlesCrawler(url="https://www.vsd.fr/sitemap_index.xml",
                                    L_keyword=sitemap_keywords)
    start = time()
    publicCrawler.save_articles("./data/public_articles_test.csv")
    vsdCrawler.save_articles("./data/vsd_articles_test.csv")
    end = time()
    print("Time elapsed:", round(end - start, 1), "seconds")

if __name__ == "__main__":
    main()