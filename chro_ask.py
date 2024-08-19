from  Vllm import Vllm
from class_chromadb import Chromadb
from config import  vllm_config, chromadb_config, mysql_config
class RAG_SQL(Vllm, Chromadb):
    def __init__(self):
        Chromadb.__init__(self)
        Vllm.__init__(self,vllm_config)
def main():
    rag = RAG_SQL()

    question = "2024年上半年内科系统门急诊收入是多少？"

    rag.index_info = rag.get_similar_index(question)
    rag.document_info = rag.get_similar_document(question)
    rag.example_info = rag.get_similar_examples(question)

    rag.connect_to_mysql(**mysql_config)

    rag.ask(question)


if  __name__  == "__main__":
    main()


