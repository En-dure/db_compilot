import hashlib
import uuid
from typing import List
import json
import chromadb
import pandas as pd
from chromadb.utils import embedding_functions
from config import chromadb_config


class Chromadb():
    def __init__(self, config=None):
        if config == None:
            self.config = chromadb_config
        default_ef = embedding_functions.DefaultEmbeddingFunction()
        self.embedding_function = self.config.get("embedding_function", default_ef)
        self.curr_client = self.config.get("client", "persistent")
        self.prefix_dir = self.config.get("prefix_dir", "")
        self.index_file = self.config.get("index_file", "")
        self.document_file = self.config.get("document_file", "")
        self.example_file = self.config.get("example_file", "")
        self.SQL_DDL_file = self.config.get("SQL_DDL_file", "")
        self.document_result = self.config.get("document_result", 5)
        self.example_result = self.config.get("example_result", 1)
        self.index_result = self.config.get("index_result", 5)
        self.ddl_result = self.config.get("ddl_result", 5)
        if self.curr_client == 'persistent':
            self.chroma_client = chromadb.PersistentClient(path='./chromedb')
        collection_metadata = None
        self.document_collection = self.chroma_client.get_or_create_collection(
            name='document',
            embedding_function=self.embedding_function,
            metadata=collection_metadata
        )
        self.ddl_collection = self.chroma_client.get_or_create_collection(
            name='ddl',
            embedding_function=self.embedding_function,
            metadata=collection_metadata
        )
        self.index_collection = self.chroma_client.get_or_create_collection(
            name='index',
            embedding_function=self.embedding_function,
            metadata=collection_metadata
        )
        self.example_collection = self.chroma_client.get_or_create_collection(
            name='example',
            embedding_function=self.embedding_function,
            metadata=collection_metadata
        )

    def generate_embedding(self, data: str, **kwargs) -> List[float]:
        embedding = self.embedding_function([data])
        if len(embedding) == 1:
            return embedding[0]
        return embedding

    def generate_uuid(self, content):
        if isinstance(content, str):
            content_bytes = content.encode("utf-8")
        elif isinstance(content, bytes):
            content_bytes = content
        else:
            raise ValueError(f"Content type {type(content)} not supported !")

        hash_object = hashlib.sha256(content_bytes)
        hash_hex = hash_object.hexdigest()
        namespace = uuid.UUID("00000000-0000-0000-0000-000000000000")
        content_uuid = str(uuid.uuid5(namespace, hash_hex))
        return content_uuid

    def add_document_data(self, document):
        id = self.generate_uuid(document) + "-doc"
        self.document_collection.add(
            documents=document,
            embeddings=self.generate_embedding(document),
            ids=id,
        )
        return id

    def add_index_data(self, index):
        id = self.generate_uuid(index) + "-index"
        self.index_collection.add(
            documents=index,
            embeddings=self.generate_embedding(index),
            ids=id,
        )
        return id

    def add_example_data(self, example):
        question = example['question']
        id = self.generate_uuid(question) + "-example"
        self.example_collection.add(
            documents=question,
            embeddings=self.generate_embedding(question),
            metadatas={"SQL": example['SQL']},
            ids=id,
        )
        return id

    def get_examples(self, example_file_path=None):
        if not example_file_path:
            example_file_path = self.prefix_dir + self.example_file
        with open(example_file_path, 'r', encoding='utf-8') as f:
            examples = json.load(f)
            examples = examples["examples"]
        return examples

    def get_document(self, document_file_path=None):
        if not document_file_path:
            document_file_path = self.prefix_dir + self.document_file
        with open(document_file_path, 'r', encoding='utf-8') as f:
            text = f.read()
            document = text.split(';\n')
        return document

    def get_index(self, index_file_path=None):
        if not index_file_path:
            index_file_path = self.prefix_dir + self.index_file
        with open(index_file_path, 'r', encoding='utf-8') as f:
            text = f.read()
            index = text.split(';\n')
        return index

    @staticmethod
    def _extract_documents(query_results, example=False) -> List:
        if query_results is None:
            return []
        if "documents" in query_results:
            documents = query_results["documents"]
            if example:
                sql = query_results["metadatas"]
                result = [[q,s] for q, s in zip(documents[0], sql[0])]
            else:
                result = documents[0]
            return result
    def get_similar_question_sql(self, question: str, **kwargs) -> list:
        result = self.example_collection.query(
                query_texts=[question],
                n_results=self.example_result,
            )
        final= Chromadb._extract_documents(result, example=True)
        return final

    def get_similar_index(self, question: str, **kwargs) -> list:
        result = self.index_collection.query(
                query_texts=[question],
                n_results=self.index_result,
            )
        return Chromadb._extract_documents(result)

    def get_similar_document(self, question: str, **kwargs) -> list:
        result = self.document_collection.query(
                query_texts=[question],
                n_results=self.document_result,
            )
        return Chromadb._extract_documents(result)

    def get_similar_ddl(self, question: str, **kwargs) -> list:
        result = self.ddl_collection.query(
            query_texts=[question],
            n_results=self.ddl_result,
        )
        return Chromadb._extract_documents(result)

    def remove_data(self, id: str, **kwargs) -> bool:
        if id.endswith("-example"):
            self.example_collection.delete(ids=id)
            return True
        elif id.endswith("-ddl"):
            self.ddl_collection.delete(ids=id)
            return True
        elif id.endswith("-doc"):
            self.document_collection.delete(ids=id)
            return True
        elif id.endswith("-index"):
            self.index_collection.delete(ids=id)
            return True
        else:
            return False

    def remove_collection(self, collection_name: str) -> bool:
        """
        This function can reset the collection to empty state.

        Args:
            collection_name (str): sql or ddl or documentation

        Returns:
            bool: True if collection is deleted, False otherwise
        """
        if collection_name == "example":
            self.chroma_client.delete_collection(name="example")
            self.example_collection = self.chroma_client.get_or_create_collection(
                name="example", embedding_function=self.embedding_function
            )
            return True
        elif collection_name == "ddl":
            self.chroma_client.delete_collection(name="ddl")
            self.ddl_collection = self.chroma_client.get_or_create_collection(
                name="ddl", embedding_function=self.embedding_function
            )
            return True
        elif collection_name == "document":
            self.chroma_client.delete_collection(name="document")
            self.document_collection = self.chroma_client.get_or_create_collection(
                name="document", embedding_function=self.embedding_function
            )
            return True
        elif collection_name == "index":
            self.chroma_client.delete_collection(name="index")
            self.index_collection= self.chroma_client.get_or_create_collection(
                name="index", embedding_function=self.embedding_function
            )
            return True
        else:
            return False

    def get_data(self, **kwargs) -> pd.DataFrame:

        example_data = self.example_collection.get()
        df = pd.DataFrame()
        if example_data is not None:
            # Extract the documents and ids

            ids = example_data["ids"]
            # Create a DataFrame
            df_example = pd.DataFrame(
                {
                    "id": ids,
                    "question": [doc for doc in example_data["documents"]],
                    "content": [doc["SQL"] for doc in example_data["metadatas"]],
                }
            )
            df_example["training_data_type"] = "example"
            df = pd.concat([df, df_example])

        ddl_data = self.ddl_collection.get()
        if ddl_data is not None:
            documents = [doc for doc in ddl_data["documents"]]
            ids = ddl_data["ids"]
            # Create a DataFrame
            df_ddl = pd.DataFrame(
                {
                    "id": ids,
                    "question": [None for doc in documents],
                    "content": [doc for doc in documents],
                }
            )
            df_ddl["training_data_type"] = "ddl"
            df = pd.concat([df, df_ddl])

        doc_data = self.document_collection.get()
        if doc_data is not None:
            # Extract the documents and ids
            documents = [doc for doc in doc_data["documents"]]
            ids = doc_data["ids"]

            # Create a DataFrame
            df_doc = pd.DataFrame(
                {
                    "id": ids,
                    "question": [None for doc in documents],
                    "content": [doc for doc in documents],
                }
            )
            df_doc["training_data_type"] = "documentation"
            df = pd.concat([df, df_doc])

        index_data = self.index_collection.get()
        if index_data is not None:
            # Extract the documents and ids
            documents = [doc for doc in index_data["documents"]]
            ids = index_data["ids"]

            # Create a DataFrame
            df_index = pd.DataFrame(
                {
                    "id": ids,
                    "question": [None for doc in documents],
                    "content": [doc for doc in documents],
                }
            )
            df_index["training_data_type"] = "index"
            df = pd.concat([df, df_index])
        return df

if __name__ == '__main__':
    c = Chromadb()
    indexs = c.get_index()
    print(indexs)
    for index in indexs:
        c.add_index_data(index)

    examples = c.get_examples()
    print(examples)
    for example in examples:
        c.add_example_data(example)

    docs = c.get_document()
    for doc in  docs:
        c.add_document_data(doc)
    # question = "2024年上半年骨科门急诊收入同比增幅"
    # similar_example = c.get_similar_question_sql(question)
    # similar_index = c.get_similar_index(question)
    # similar_document = c.get_similar_document(question)
    c.remove_collection('document')
    c.remove_collection('example')
    c.remove_collection('index')

    df = c.get_data()
    # print(df)