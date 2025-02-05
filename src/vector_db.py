from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import certifi

uri = f"mongodb+srv://{os.getenv('whiskeydb_admin')}:{os.getenv('whiskeydb_pwd')}@{os.getenv('whiskeydb_url')}/?retryWrites=true&w=majority&appName=WhiskeyRecommender"
ca = certifi.where()

# Create a new client and connect to the server
client = MongoClient(uri,
    server_api=ServerApi('1'),
    tls=True,
    tlsAllowInvalidCertificates=False,
    tlsCAFile=ca)
# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)


collection = client["whiskey_database"]["vectordb_singleembed"]

vector_store = MongoDBAtlasVectorSearch(
   collection = collection,         # Collection to store embeddings
   embedding = embedding_model,   # Embedding model to use
   index_name = "vector_index",    # Name of the vector search index
   relevance_score_fn = "cosine"   # Similarity score function, can also be "euclidean" or "dotProduct"
)