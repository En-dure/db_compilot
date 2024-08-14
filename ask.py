from Vllm import Vllm
from config import vllm_config, mysql_config


if __name__ == "__main__":
    question = "2024年上半年骨科的门急诊收入同比增幅？"
    vllm = Vllm(vllm_config)
    vllm.connect_to_mysql(**mysql_config)
    if not question:
        question = input("请输入你的问题: ")
    vllm.ask(question)
