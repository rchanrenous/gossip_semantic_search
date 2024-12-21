from sentence_transformers import SentenceTransformer
from mistralai import Mistral
from scrap import ArticleScrapper
from typing import List
from nltk.tokenize import PunktSentenceTokenizer
from dotenv import load_dotenv
from os import getenv

class Encoder:
    '''
    Use language model to encode text.

    Attributes:
        model_name: language model name
        model: language model object
        api_key: Mistral AI API key
        mistral_client: Mistral client object
    '''
    

    def __init__(self, api_key: str=None, model_name: str='sentence-transformers/all-MiniLM-L6-v2'):
        '''
        Initalize attributes.
        '''

        if api_key is not None:
            self.model_name = 'mistral-embed'
            self.api_key = api_key
            self.mistral_client = Mistral(api_key=api_key)
        else:
            self.api_key = None
            self.model = SentenceTransformer(model_name)
    

    def encode(self, L_str: List[str]):
        '''
        Encode the argument string using the language model.

        Parameter:
            L_str: list of strings to encode

        Returns:
            embedding: numpy array containing the embedding
        '''

        if self.api_key is not None:
            response = self.mistral_client.embeddings.create(model=self.model_name,
                                                    inputs=L_str)
            return [data.embedding for data in response.data]
        else:
            embedding = self.model.encode(L_str)
            return embedding
        


    def get_sentences(self, s: str) -> List[str]:
        '''
        Split input string into sentences.

        Parameters:
            s: text to split into sentences

        Returns:
            L_sentences: list of the sentences
        '''

        tokenizer = PunktSentenceTokenizer()
        L_sentences = tokenizer.tokenize(s)
        return L_sentences


    def encode_sentences(self, s: str) -> List[List]:
        '''
        Encode the sentences of the input string.

        Parameters:
            s: text to split into sentences and encode the sentences

        Returns:
            L_encodings: list of encodings
        '''

        # extract sentences out of s
        L_sentences = self.get_sentences(s)
        # encode the sentences
        L_encodings = self.encode(L_sentences)
        return L_encodings


    def get_embedding_dimension(self):
        '''
        Get the output dimension of the language model embeddings.

        Returns:
            the output dimension of the language model embeddings
        '''

        return self.model.get_sentence_embedding_dimension()


def main():
    load_dotenv()
    MISTRAL_AI_API_KEY = getenv("MISTRAL_AI_API_KEY")
    #sentences = ["This is an example sentence", "Each sentence is converted"]
    #sentence = ["If you grew up in a time before the internet made its debut, you’ll remember it wasn’t always easy to find new things to like. We discovered new bands when we happened to hear them on the radio, we’d see a new TV show by accident because we forgot to change the channel, and we’d find a new favorite video game based almost entirely on the picture on the cover.\nNowadays, things are very different. Spotify will point me to artists that match my tastes, Netflix will highlight movies and TV shows it knows we’ll enjoy, and Xbox knows what we’ll probably want to play next. These recommendation systems make it so much easier for us to find the things we’re actually looking for, and they’re powered by nearest neighbor (NN) algorithms. NN looks at the extensive sea of information it has available and identifies the closest thing to something you like, or something you’re searching for.\nBut NN algorithms have an inherent flaw. If the amount of data they’re analyzing gets too big, crawling through every option takes forever. This is a problem, especially as these data sources get bigger and bigger every year. This is where approximate nearest neighbor (ANN) grabs the baton from NN and changes the game."]
    sentence = ["L'annonce du duo lors de la rentrée 2024 n'avait pas fait l'unanimité. Si de nombreux internautes étaient ravis de la collaboration entre le gagnant de la Star Academy, Pierre Garnier, et le gagnant de Popstars en 2003, Matt Pokora, nombreux étaient également ceux qui avaient critiqué.\nLes fans de Pierre Garnier estimaient que le jeune chanteur de 22 ans n'avait pas besoin de ça pour cartonner, tandis que d'autres estimaient que Matt Pokora voulait surfer sur la vague. Au micro de M Radio, le 20 septembre dernier, l'artiste qui a annoncé une nouvelle tournée la semaine dernière, avait déclaré :  J'ai suivi son parcours, fulgurante ascension ! J'ai aimé ce qu'il faisait, l'artiste qu'il était, sa voix etc. Quand un artiste est un bon, t'es séduit par son talent.  Tout en révélant que l'idée du duo est à l'initiative de Pierre Garnier et son équipe. Une façon de répondre aux critiques sur les réseaux sociaux.\nMatt Pokora ravi de ce succès\nQuelques semaines plus tard, les deux artistes ont collaboré ensemble sur le clip. Sur Youtube, la vidéo sortie il y a un mois, cumule 1,7 millions de vues. Et le titre Chaque Seconde vient d'atteindre un joli pallier : le duo entre Pierre Garnier et Matt Pokora est certifié Single d'Or, ce qui équivaut à 15 000 000 d'écoutes sur les plateformes de streaming.\nL'annonce vient d'être faite ce lundi 25 novembre par le Syndical National de l'Édition Phonographique (SNEP), n'a pas manqué de faire réagir le mari de Christina Milian. En story Instagram, Matt Pokora a partagé la publication en identifiant Pierre Garnier, tout en y ajoutant un émoji où deux mains se serrent." ]
    scrapper = ArticleScrapper()
    L_article = []
    L_article.append(scrapper.scrap("https://www.public.fr/une-etude-revele-la-couleur-des-yeux-des-personnes-les-plus-intelligentes-mythe-ou-realite"))
    L_article.append(scrapper.scrap(url="https://vsd.fr/22837-recensement-etes-vous-fils-de-resistant/"))
    encoder = Encoder(api_key=MISTRAL_AI_API_KEY)
    encoder = Encoder()
    L_embeddings = encoder.encode(L_article)
    print(L_embeddings.shape, type(L_embeddings), len(L_embeddings[0]))
    L_sentences = encoder.get_sentences(L_article[0])
    L_sentence_embeddings = encoder.encode_sentences(L_article[0])
    print(len(L_sentence_embeddings), len(L_sentence_embeddings[0]))

if __name__ == "__main__":
    main()