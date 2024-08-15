from Vllm import Vllm
from config import vllm_config, mysql_config


def ask_question_list():
    with open("question.txt", 'r', encoding='utf-8') as f:
        questions = f.read()
        question = [q for q in questions.split("？\n") if q != ""]
    vllm = Vllm(vllm_config)
    vllm.connect_to_mysql(**mysql_config)
    for q in question:
        vllm.ask(q)



if __name__ == "__main__":
    # question = "2024年1-6月骨科住院收入较2023年同期增幅多少？"
    #
    # vllm = Vllm(vllm_config)
    # vllm.connect_to_mysql(**mysql_config)
    # if not question:
    #     question = input("请输入你的问题: ")
    # vllm.ask(question)
    ask_question_list()