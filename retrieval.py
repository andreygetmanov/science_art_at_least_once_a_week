import os
import torch
import json

from transformers import AutoTokenizer, AutoModelForQuestionAnswering
from transformers import AutoTokenizer, pipeline

from typing import List

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document


class JSONDocumentLoader(BaseLoader):
    '''
    JSON document loader class
    '''

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path

    def load(self) -> List[Document]:
        data = json.load(
            open(self.file_path, 'r', encoding='utf-8')
        )
        dataset = []
        for key in data:
            metadata = data[key]
            metadata["key"] = key
            content = metadata["description_ru"]
            del metadata["description_ru"]

            entry = Document(
                page_content=content,
                metadata=metadata,
            )
            dataset.append(entry)
            
        return dataset

def load_vector_db(file_path, use_splitter = True, chunk_size=2000, chunk_overlap=150):
    '''
    Loads vector database with given chunk size and overlap, splitting can be disabled
    '''
    loader = JSONDocumentLoader(file_path)
    docs = loader.load()
    if use_splitter:
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        docs = text_splitter.split_documents(docs)
    return docs

def init_retriever(docs, modelPath = "cointegrated/rubert-tiny2"):
    '''
    Inits and returns retriever object with given embedding model (RuBert-tiny2 by defult)
    '''
    model_kwargs = {'device':'cuda'}
    encode_kwargs = {'normalize_embeddings': False}
    embeddings = HuggingFaceEmbeddings(
        model_name=modelPath, 
        model_kwargs=model_kwargs, 
        encode_kwargs=encode_kwargs 
    )
    db = FAISS.from_documents(docs, embeddings)
    retriever = db.as_retriever()
    return retriever

def get_top_k(retriever, query, query_ind = "", k = 3):
    '''
    Returns up to top K relevant documents
    Query indices are remaining str, not ind
    '''
    docs = retriever.get_relevant_documents(query)
    docs = [doc for doc in docs if doc.metadata["key"] != query_ind][:k]
    return docs
    
#Example usage

# import random

# source = 'science_art_at_least_once_a_week-master/ars_electronica_prizewinners_ru.json'
# path = 'science_art_at_least_once_a_week-master/not_posted.txt'
# docs_db = load_vector_db(source)
# retriever = init_retriever(docs_db)

# data = json.load(open(source, 'r', encoding='utf-8'))
# not_posted = open(path, 'r').readline().split(',')
# key = random.choice(not_posted)
# print(f'Key is {key}')
# artwork = data[key]

# print("Source:\n")
# print(artwork["description_ru"], "\n")
# res = get_top_k(retriever, artwork['description_ru'], key, 3)

# print("Recs:\n")
# for example in res:
#     print(example.page_content, "\n")