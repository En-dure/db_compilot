vllm_config = {
    "auth-key": "1234",
    "vllm_host": "http://192.168.20.126:8866",
    "model": "qwen/Qwen2-72B-Instruct"
}

mysql_config = {
    "host": "192.168.20.126",
    "user": "root",
    "password": "123456",
    "dbname": "ten_hospital",
    "port": 3306,
}

base_config = {
    "log_dir": "log.log",
    "dialect": "SQL",
    "semantic_dir": "semantic.txt",
    "prefix_dir": "addition/",
    "index_file": "index.txt",
    "document_file": "document.txt",
    "SQL_DDL_file": "create_tables.sql",
    "example_file": "example.txt"
}
