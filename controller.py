from fastapi import HTTPException, Query, Path, Body, APIRouter, Depends, UploadFile, File
from typing import List
import asyncpg
import aiofiles
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
import uuid
import os
import uuid
from datetime import datetime

from models import CollectionData, AddText, AddFile, AddRepo, QueryText
from postgres import get_postgres
from filehelper import FileHelper
from chroma_client import ChromaDBClient

router = APIRouter()

embed_model = SentenceTransformer("all-mpnet-base-v2")
db_client = ChromaDBClient(embed_model = "all-mpnet-base-v2")
filehelper = FileHelper()
upload_dir = "UploadedRepoFiles"
os.makedirs(upload_dir, exist_ok=True)

def chunk_text(text, chunk_size=300, chunk_overlap=20):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len
    )
    return splitter.split_text(text)

@router.post("/upload/")
async def upload_files(
    repoName: str = Body(..., description="Repo name"),
    files: List[UploadFile] = File(...),
    db_pool: asyncpg.Pool = Depends(get_postgres)
    ):
    file_records = []

    for file in files:
        unique_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{unique_id}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        try:
            async with aiofiles.open(file_path, "wb") as out_file:
                content = await file.read()
                await out_file.write(content)
            await insert_repo_files_db(repoName, file.filename, unique_filename, db_pool)
            file_records.append((file.filename, unique_filename))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error saving file {file.filename}: {str(e)}")
    
    return {"message": "Files uploaded successfully", "files": [record[0] + ":" + record[1]  for record in file_records]}

@router.post("/create_collection")
def create_collection(data: CollectionData):
    try:
        db_client.create_collection(name=data.name, metadata=data.metadata)
        return {"message": "Collection created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/add_text")
def add_text(data: AddText):
    try:
        file_id = str(uuid.uuid4())
        chunks = chunk_text(data.text)
        for idx, chunk in enumerate(chunks):
            #embedding = model.encode(chunk).tolist()
            db_client.add_text(
                collection_name=data.collection_name,
                document_id=f"{file_id}_chunk_{idx}",
                text=[chunk],
                metadata=data.metadata
            )
        return {"message": "text added successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/add_file")
def add_file(data: AddFile):
    try:
        extension = os.path.splitext(data.file_path)[1]
        text = ""
        if extension == ".pdf":
            text = filehelper.extract_text_from_pdf(data.file_path)
        elif extension == ".docx":
            text = filehelper.read_docx(data.file_path)
        else:
            text = filehelper.read_text_content(data.file_path)

        file_id = os.path.splitext(os.path.basename(data.file_path))[0]
        chunks = chunk_text(text)
        for idx, chunk in enumerate(chunks):
            #embedding = model.encode(chunk).tolist()
            db_client.add_text(
                collection_name=data.collection_name,
                document_id=f"{file_id}_chunk_{idx}",
                text=chunk,
                metadata=data.metadata
            )
        return {"message": "file content added successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def get_addfile(collection_name, file_path, metadata) -> AddFile:
    return AddFile(collection_name=collection_name, file_path=file_path, metadata=metadata)

@router.post("/add_repo")
async def add_repo(data: AddRepo, db_pool: asyncpg.Pool = Depends(get_postgres)):
    try:
        repo_files = await get_files_by_reponame(reponame=data.repo_name, db_pool=db_pool)
        print(repo_files)
        for file_name in repo_files:
            try:
                file_path = os.path.join(upload_dir, file_name)
                print(file_path)
                add_file(get_addfile(collection_name = data.repo_name.replace(" ", "_"),
                                     file_path = file_path, 
                                     metadata = data.metadata))
                await update_embeddingstatus(file_name, "success", db_pool)
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
                await update_embeddingstatus(file_name, "failure", db_pool)
        return {"message": "embeddings created for the mentioned repo"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/query_text")
def query_text(data: QueryText):
    try:
        results = db_client.query_text(
            collection_name=data.collection_name,
            query_text=data.query_text,
            n_results=data.n_results
        )
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/list_collections")
def list_collections():
    try:
        collections = db_client.list_collections()
        return {"collections": collections}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.get("/view_collection/")
def view_collection(collection_name: str):
    try:
        return db_client.view_collection(collection_name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/get_files", response_model=List[str])
async def get_files_by_reponame(
    reponame: str = Query(...),
    db_pool: asyncpg.Pool = Depends(get_postgres),
) -> List[str]:
    query = """
        SELECT unique_filename FROM addrepository
        WHERE reponame = $1 and (indexed = false or (indexed = true and embedding_status = 'failure'))
    """
    try:
        async with db_pool.acquire() as conn:
            results = await conn.fetch(query, reponame)
            return [result['unique_filename'] for result in results]
    except Exception as e:
        print(f"Error filtering files by repo: {e}")
        raise HTTPException(
            status_code=500, detail="Internal server error during file filtering"
        )
    
@router.put("/update_embeddingstatus", response_model=str)
async def update_embeddingstatus(
    unique_filename: str = Query(...),
    status: str = Query(...),
    db_pool: asyncpg.Pool = Depends(get_postgres),
) -> str:
    query = """
        UPDATE addrepository
        SET embedding_status = $1, indexed = true where unique_filename = $2
    """
    try:
        async with db_pool.acquire() as conn:
            result = await conn.fetchrow(query, status, unique_filename)
            return "status updated!"
    except Exception as e:
        print(f"Error updating status by filename: {e}")
        raise HTTPException(
            status_code=500, detail="Internal server error during updating status by filename"
        )
    
async def insert_repo_files_db(
    reponame : str,
    original_file_name : str,
    unique_file_name : str,
    db_pool: asyncpg.Pool = Depends(get_postgres),
) -> str:
    query = """
        INSERT INTO addrepository (reponame, original_filename, unique_filename, indexed, timestamp, embedding_status)
        VALUES ($1, $2, $3, $4, $5, $6)
    """
    try:
        async with db_pool.acquire() as conn:
            result = await conn.execute(query, reponame, original_file_name, unique_file_name, False, datetime.now(), "")
            return "file added!"
    except Exception as e:
        print(f"Error inserting repo data: {e}")
        raise HTTPException(
            status_code=500, detail="Internal server error during inserting repo data"
        )