from pydantic import BaseModel

class CollectionData(BaseModel):
    name: str
    metadata: dict = {}

class AddText(BaseModel):
    collection_name: str
    #document_id: str
    #embedding: list
    text: str
    metadata: dict = {}

class AddFile(BaseModel):
    collection_name: str
    file_path: str
    metadata: dict = {}

class AddRepo(BaseModel):
    repo_name: str
    metadata: dict = {}

class QueryText(BaseModel):
    collection_name: str
    query_text: str
    n_results: int = 5