from Vllm import Vllm
from config import vllm_config, mysql_config
import  json

if __name__ == "__main__":

    question = "2023年各个科室的医疗收入"
    vllm = Vllm(vllm_config)
    if not question:
        question = input("请输入你的问题: ")
    while True:
        semantic_prompt = vllm.get_semantic_prompt(question)
        semantic = vllm.submit_semantic_prompt(semantic_prompt)
        semantic_result = json.loads(semantic)
        print(semantic_result)
        if semantic_result["Done"] == "False":
            question = input("请重新输入你的问题: ")
        else:
            semantic_result = str(semantic_result["result"])
            break
    thinking = vllm.get_thinking_prompt(question, semantic_result)
    thinking_result = vllm.submit_thinking_prompt(thinking)
    thinking_result = json.loads(thinking_result)
    if thinking_result["Done"] == "False":
        print(thinking_result["res"])
    else:
        thinking_result = thinking_result["res"]

    # prompt = vllm.get_sql_prompt(question)
    # answer = vllm.submit_prompt(prompt)
# print(answer)


