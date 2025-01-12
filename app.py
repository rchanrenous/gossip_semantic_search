import streamlit as st
from embeddings import Embeddings
from scrap import ArticleScrapper
from encode import Encoder
from dotenv import load_dotenv
from os import getenv
from pandas import DataFrame

@st.cache_resource
def setup():
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
    return embeddings

embeddings = setup()

st.title("👋 Welcome to the Gossip Search Engine")

st.write("Type in any query to get relevant gossip articles. Try 'Angelina Jolie et Brad Pitt sont-ils toujours ensemble?' for instance 👀")

st.text_input("Your query:", key="query")

st.slider("How many answers would you like?",
            min_value=1,
            max_value=50,
            key="nb_answers")

if st.session_state.query != "":
    df_res = DataFrame(embeddings.search(embeddings.encoder.encode([st.session_state.query])[0],
                                            top_k=st.session_state.nb_answers),
                        columns=["Date", "Article", "Article Relevance Score", "Most relevant sentence", "Sentence Relevance Score"])
    st.dataframe(df_res, column_order="")





