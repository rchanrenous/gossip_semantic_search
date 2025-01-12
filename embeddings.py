from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from qdrant_client.models import PointStruct, Batch
from scrap import ArticleScrapper
from encode import Encoder
from time import time
from typing import List
from sklearn.neighbors import NearestNeighbors
import csv
from os.path import isfile
from urllib.error import URLError
from dotenv import load_dotenv
from os import getenv


class Embeddings:
    '''
    Class to get the article embeddings and store them in Qdrant.

    Attributes:
        scrapper: ArticleScrapper object to retrieve the article contents from the URLs
        encoder: ArticleEncoder object to encode the article contents
        collection_name: collection name in Qdrant
        qdrant_client: Qdrant client to access the database
    '''


    def __init__(self, qdrant_url: str, api_key: str, collection_name: str, scrapper: ArticleScrapper, encoder: Encoder):
        '''
        Initialize the attributes and create the collection in the Qdrant database.

        Parameters:
            qdrant_url: URL of the Qdrant database
            api_key: API key of the Qdrant database
            collection_name: name of the collection in Qdrant
            scrapper: ArticleScrapper object
            encoder: Encoder object
        '''

        self.scrapper = scrapper
        self.encoder = encoder
        self.collection_name = collection_name
        self.qdrant_client = QdrantClient(url=qdrant_url,
                                            api_key=api_key)
        if not self.qdrant_client.collection_exists(self.collection_name):
            print("Creating collection:", self.collection_name)
            self.qdrant_client.create_collection(collection_name=self.collection_name,
                                vectors_config=VectorParams(size=384,
                                                            distance=Distance.DOT))
        else:
            print("Collection exists:", self.collection_name)
            print("Number of points in DB:", self.get_point_count())


    def get_point_count(self) -> int:
        '''
        Get the number of points in the collection.
        '''

        return (self.qdrant_client.count(self.collection_name, exact=True).count)

    def get_non_inserted_articles_count(self, url_file_name: str) -> int:
        '''
        Get the number of files which were not inserted in the database.

        Parameters:
            url_file_name: name of the URL file

        Returns:
            nb_not_inserted: the aforementioned count
        '''

        nb_not_inserted = 0
        # count the number of files that were ignored because too long
        url_file_name_ignored = f"{url_file_name[:url_file_name.find('.')]}_ignored.csv"
        if isfile(url_file_name_ignored):
            with open(url_file_name_ignored, "r") as f_ignored:
                nb_ignored = len(f_ignored.readlines())
                nb_not_inserted += nb_ignored
                print("\tAccounting for the", nb_ignored, "ignored files")
        # count the number of files whose resource is not accessible anymore (410 error)
        url_file_410_error = f"{url_file_name[:url_file_name.find('.')]}_http_error_410.csv"
        if isfile(url_file_410_error):
            with open(url_file_410_error, "r") as f_410:
                nb_410_error = len(f_410.readlines())
                nb_not_inserted += nb_410_error
                print("\tAccounting for the", nb_410_error, "410 error files")
        # return the total count
        return nb_not_inserted


    def get_url_list(self, url_file_name: str,
                            offset: int=-1,
                            nb_embeddings: int=-1,
                            verbose: bool=True) -> List[str]:
        '''
        Get an URL list from the argument file, starting at the specified offset in the file and returning a certain number of URLs.

        Parameters:
            url_file_name: name of the file containing the URLs
            offset: index (starting at 0) where to start returning the URLs; -1 or 0 means starting from the beginning
            b_embeddings: number of URLs to return in the list; -1 means returning all the URLs starting from the offset
            verbose: True for information output, else False
        '''

        assert nb_embeddings == -1 or nb_embeddings > 0, "Invalid number of embeddings"
        assert offset >= -1, "Invalid URL dataset offset"
        if verbose == True:
            if offset > 0 and nb_embeddings > 0:
                print(f"{url_file_name}: getting URLs #{offset} to #{offset + nb_embeddings}")
            elif offset > 0:
                print(f"{url_file_name}: getting URLs from #{offset}")
            elif nb_embeddings > 0:
                print(f"{url_file_name}: getting URLs until #{nb_embeddings}")
            else:
                print(f"{url_file_name}: getting all URLs")
        with open(url_file_name) as f:
            L_url = []
            # get the file pointer to the offset
            if offset > 0:
                # get the true offset
                offset += self.get_non_inserted_articles_count(url_file_name)
                for i in range(offset):
                    line = f.readline()
                    if line == "\n" or line == "":
                        if verbose == True:
                            print(f"\tReached end of file: URL #{i - 1}")
                        return L_url
            # get the right number of URLs
            if nb_embeddings > 0:
                for i in range(nb_embeddings):
                    line = f.readline()
                    if line == "\n" or line == "":
                        if verbose:
                            print(f"\tReached end of file: URL #{offset + i - 1 if offset > 0 else i - 1}")
                        return L_url
                    else:
                        L_url.append(line)
                return L_url
            else:
                return f.readlines()


    def get_embeddings(self, url_file_name: str,
                                offset: int=-1,
                                nb_embeddings: int=-1,
                                max_token: int=1200,
                                batch_size_encode: int=5,
                                batch_size_insert: int=100,
                                verbose: int=100) -> None:
        '''
        Scrap the article contents from the URLs in the input file, encode the contents, insert the resulting embeddings in the database.
        Work is done in batches.

        Parameters:
            url_file_name: file containing the list of article URLs
            batch_size: batch size of the articles to process at once
            verbose: frequency of current state displaying (non-positive for no display)
        '''

        assert batch_size_encode <= batch_size_insert and batch_size_insert % batch_size_encode == 0, "Encoding and Insertion batch sizes incompatible"
        start = time()
        scrapper = ArticleScrapper(paragraph_tag_name="p")
        i = 0
        L_article = []
        L_payload = []
        L_vector = []
        L_id = []
        L_ignored = []
        L_410_error = []
        id_start = self.get_point_count()
        with open(url_file_name) as url_file:
            # get list of the article URLs
            L_url = self.get_url_list(url_file_name, offset, nb_embeddings)
            # scrap each URL, encode them in batches and insert them in batches into the database
            for url in L_url:
                url = url.rstrip()
                # scrap each URL
                try:
                    article = self.scrapper.scrap(url)
                    l = len(article.split(" "))
#print(i,l, url)
                    if len(article.split(" ")) < max_token:
                        L_article.append(self.scrapper.scrap(url))
                        L_payload.append({"url": url})
                        i += 1
                    else:
                        L_ignored.append(url)
                # catch 410 errors
                except URLError as err:
                    if err.code == 410:
                        L_410_error.append(url)
                if verbose > 0 and i % verbose == 0:
                    print(f"\t{url_file_name}: scrapped article: {i + offset if offset > -1 else i}, time elapsed: {round(time() - start, 1)} sec")
                # encode article contents in batches
                if i % batch_size_encode == 0 and len(L_article) > 0:
                    L_vector += self.encoder.encode(L_article)
                    L_id += range(i - batch_size_encode + 1 + id_start, i + 1 + id_start)
                    L_article = []
                # insert batches of encodings in batches into the database
                if i % batch_size_insert == 0 and len(L_vector) > 0:
                    self.qdrant_client.upsert(collection_name=self.collection_name,
                                                points=Batch(ids=L_id,
                                                                vectors=L_vector,
                                                                payloads=L_payload))
                    print(f"\t{url_file_name}: inserted article embedding:", i + offset if offset > -1 else i)
                    L_vector = []
                    L_id = []
                    L_payload = []
					# update the ignored files list
                    if len(L_ignored) != 0:
                        with open(f"{url_file_name[:url_file_name.find('.')]}_ignored.csv", "a") as f:
                            writer = csv.writer(f)
                            writer.writerow([url])
                            print("Article too long, added to ignored articles file:", url)
                        L_ignored = []
					# update the 410 error files list
                    if len(L_410_error) != 0:
                        with open(f"{url_file_name[:url_file_name.find('.')]}_http_error_410.csv", "a") as f:
                            writer = csv.writer(f)
                            writer.writerow([url])
                            print(f"\t{url}: error 410, added file to 410 error URL file")
                        L_410_error = []
        # encode remaining articles 
        nb_insert = len(L_article)
        if nb_insert != 0:
            L_vector += self.encoder.encode(L_article)
            L_id += range(i - nb_insert + 1 + id_start, i + 1 + id_start)
        # insert remaining embeddings into the database
        if len(L_vector) != 0:
            self.qdrant_client.upsert(collection_name=self.collection_name,
                                           points=Batch(ids=L_id,
                                                            vectors=L_vector,
                                                            payloads=L_payload))
        print("Done enconding articles from:", url_file_name)
    

    def search(self, query_vector: List[float], top_k: int=1) -> List[tuple]:
        '''
        Find closest vector(s) in the collection to the vector passed in argument.

        Parameters:
            query_vector: query vector to search the closest vector(s)
            top_k: number of closest vectors to return

        Returns:
            L_result: list of tuples containing the URL corresponding to the closest vector, the similarity score of the output vector with the query vector, the closest sentence in the article to the query vector and its similarity score.  
        '''

        L_result_article = self.qdrant_client.search(collection_name=self.collection_name,
                                                        query_vector=query_vector,
                                                        limit=top_k)
        L_result_article = [(res.payload["url"], res.score) for res in L_result_article]
        L_result = []
        for (url, score) in L_result_article:
            # get embeddings of each sentence from the article
            article = self.scrapper.scrap(url=url)
            L_sentences = self.encoder.get_sentences(article)
            L_vectors = self.encoder.encode(L_sentences)
            date = self.scrapper.scrap_date(url)
            # search for sentence embedding in the article closest to the query vector
            nn = NearestNeighbors(n_neighbors=1).fit(L_vectors)
            sentence_score, indice = nn.kneighbors([query_vector])
            L_result.append((date, url, score, L_sentences[int(indice[0][0])], float(sentence_score[0][0]))) 
        # return list of (date, url, url_score, sentence, sentence_score)
        return L_result


def main():
    # get config from .env
    load_dotenv()
    QDRANT_URL = getenv("QDRANT_URL")
    QDRANT_API_KEY = getenv("QDRANT_API_KEY")
    MISTRAL_AI_API_KEY = getenv("MISTRAL_AI_API_KEY")

    scrapper = ArticleScrapper()
    #encoder = Encoder(api_key=MISTRAL_AI_API_KEY)
    encoder = Encoder()
    embeddings = Embeddings(qdrant_url=QDRANT_URL,
                                api_key=QDRANT_API_KEY,
                                collection_name="gossip_articles_embeddings_sentence_transformers",
                                scrapper=scrapper,
                                encoder=encoder)
    '''
    print(embeddings.qdrant_client.get_collections())
    for col in embeddings.qdrant_client.get_collections():
        for c in col[1]:
            embeddings.qdrant_client.delete_collection(collection_name=c.name)
    '''
    '''
    embeddings.get_embeddings(url_file_name="data/sample_vsd.csv",
                                batch_size_encode=5, batch_size_insert=100,
                                verbose=5)
    '''
    public_articles_file = "data/public_articles.csv"
    vsd_articles_file = "data/vsd_articles.csv"
    offset = embeddings.get_point_count()
    embeddings.get_embeddings(url_file_name=public_articles_file,
                                offset=offset,
                                nb_embeddings=-1,
                                batch_size_encode=5,
                                batch_size_insert=100,
                                verbose=50)
    offset = embeddings.get_point_count()
    with open(public_articles_file, "r") as f:
        reader = csv.reader(f)
        nb_articles_public = len(list(reader))
    public_ignored_file = f"{public_articles_file[:public_articles_file.find('.')]}_ignored.csv"
    if isfile(public_ignored_file):
        with open(public_ignored_file, "r") as f:
            reader = csv.reader(f)
            nb_articles_public -= len(list(reader))
    public_410_file = f"{public_articles_file[:public_articles_file.find('.')]}_http_error_410.csv"
    if isfile(public_ignored_file):
        with open(public_410_file, "r") as f:
            reader = csv.reader(f)
            nb_articles_public -= len(list(reader))
    print("Encoding VSD articles...")
    embeddings.get_embeddings(url_file_name=vsd_articles_file,
                                offset=offset - nb_articles_public,
                                nb_embeddings=-1,
                                batch_size_encode=5,
                                batch_size_insert=100,
                                verbose=50)
    '''
    print("Number of points in collection:", embeddings.get_point_count())
    L_res = embeddings.search(embeddings.encoder.encode(["pourquoi brad pitt et angelina jolie ne sont plus ensemble?"])[0], top_k=3)
    print(L_res)
    '''
    

if __name__ == "__main__":
    main()
