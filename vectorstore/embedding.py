import os
from dotenv import load_dotenv
from llama_index.embeddings.openai import OpenAIEmbedding

load_dotenv()

def get_embedding_model():

    return OpenAIEmbedding(
        model="text-embedding-3-small",
        api_key=os.getenv("OPENAI_API_KEY")
    )