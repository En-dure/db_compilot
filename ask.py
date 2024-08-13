from Vllm import Vllm
from config import vllm_config, mysql_config

question = None
vllm = Vllm(vllm_config)
if not question:
    question = input("请输入你的问题:")

prompt = vllm.get_sql_prompt(question)
answer = vllm.submit_prompt(prompt)
print(answer)

