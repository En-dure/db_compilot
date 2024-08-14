from Vllm import Vllm
from config import vllm_config, mysql_config
import  json

if __name__ == "__main__":
    question = "2024年上半年骨科的门急诊均次费变动的影响（%）"
    vllm = Vllm(vllm_config)
    if not question:
        question = input("请输入你的问题: ")
    while True:
        semantic_prompt = vllm.get_semantic_prompt(question)
        semantic = vllm.submit_semantic_prompt(semantic_prompt)
        semantic_result = json.loads(semantic)
        print("semantic", semantic_result)
        if semantic_result["Done"] == "False":
            question = input("请重新输入你的问题: ")
        else:
            semantic_result = str(semantic_result["result"])
            print("semantic_result", semantic_result)
            break
    thinking = vllm.get_thinking_prompt(question, semantic_result)
    thinking_result = vllm.submit_thinking_prompt(thinking)
    thinking_result = json.loads(thinking_result)
    if thinking_result["Done"] == "False":
        print("thinking_result:", thinking_result["res"])
    else:
        thinking_result = thinking_result["res"]
        print("thinking_result:", thinking_result)
    sql_prompt = vllm.get_sql_prompt(question, thinking_result)
    initial_sql = vllm.submit_prompt(sql_prompt)
    print("initial_sql:", initial_sql)
    reflection_prompt = vllm.get_reflection_prompt(question, thinking_result, initial_sql)
    reflection = vllm.submit_reflection_prompt(reflection_prompt)
    print("reflection:", reflection)
