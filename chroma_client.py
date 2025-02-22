import chromadb
from chromadb.utils import embedding_functions

class ChromaDBClient:
    def __init__(self, embed_model, db_path="\data"):
        self.client = chromadb.PersistentClient(path=db_path)
        sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name = embed_model
        )
        self.embed_function = sentence_transformer_ef
    
    def create_collection(self, name, metadata={}):
        return self.client.create_collection(name=name, metadata=metadata, embedding_function=self.embed_function)
    
    def add_text(self, collection_name, document_id, text, metadata={}):
        if collection_name not in self.list_collections():
            self.create_collection(collection_name, metadata)
        collection = self.client.get_collection(name=collection_name)
        collection.add(ids=[document_id], documents=[text], metadatas=[metadata])
    
    def query_text(self, collection_name, query_text, n_results=5):
        collection = self.client.get_collection(name=collection_name)
        return collection.query(query_texts=[query_text], n_results=n_results)
    
    def list_collections(self):
        return [col.name for col in self.client.list_collections()]
    
    def view_collection(self, collection_name):
        collection = self.client.get_collection(name=collection_name)
        stored_data = collection.get()
        
        response = {
            "document_ids": stored_data["ids"],
            "documents": stored_data["documents"],
            "embeddings": stored_data.get("embeddings", [])  # Optional, remove if embeddings are large
        }
        return response