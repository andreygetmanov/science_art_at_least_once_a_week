import json
from typing import List

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document


class JSONDocumentLoader(BaseLoader):
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path

    def load(self) -> List[Document]:
        with open(self.file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        dataset = []
        for key in data:
            metadata = data[key]
            metadata["key"] = key
            content = metadata.pop("description_ru", "")
            dataset.append(Document(page_content=content, metadata=metadata))
        return dataset


class VectorDB:
    def __init__(
        self,
        file_path: str,
        model_path: str = "cointegrated/rubert-tiny2",
        chunk_size=2000,
        chunk_overlap=150,
    ):
        self.file_path = file_path
        self.model_path = model_path
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.docs = []
        self.embeddings = None
        self.db = None

    def load(self, splitter=RecursiveCharacterTextSplitter):
        loader = JSONDocumentLoader(self.file_path)
        self.docs = loader.load()
        if splitter:
            text_splitter = splitter(
                chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap
            )
            self.docs = text_splitter.split_documents(self.docs)

    def init_embeddings(self):
        model_kwargs = {"device": "cuda"}
        encode_kwargs = {"normalize_embeddings": False}
        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.model_path,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs,
        )

    def create_db(self):
        if not self.embeddings:
            self.init_embeddings()
        self.db = FAISS.from_documents(self.docs, self.embeddings)

    def get_retriever(self):
        if not self.db:
            self.create_db()
        return self.db.as_retriever()


class Retriever:
    def __init__(self, vector_db: VectorDB):
        self.retriever = vector_db.get_retriever()

    def get_top_k(self, query, query_ind="", k=3):
        docs = self.retriever.get_relevant_documents(query)
        docs = [doc for doc in docs if doc.metadata["name"] != query_ind][:k]
        return docs
