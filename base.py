from abc import ABC, abstractmethod
from typing import List, Tuple, Union
import logging
from config import base_config
class Base(ABC):
    def __init__(self, config=base_config):
        self.config = config
        self.dialect = self.config.get("dialect", "SQL")
        self.log_dir = self.config.get("log_dir", "log.log")
        self.logger = self.setup_logger(self.log_dir)
    def setup_logger(self, log_file: str, name: str = __name__, level: str = "INFO"):
        logger = logging.getLogger(name)
        if not logger.hasHandlers():
            logger.setLevel(level)

            # 添加文件处理器
            file_handler = logging.FileHandler(log_file)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        return logger
    def log(self, logger, message:str, title: str = "Info"):
        log_method = getattr(logger, title.lower(), logger.info)
        log_method(message)

    def get_initial_prompt(self, message) -> str:
        if isinstance(message, str):
            try:
                with open(message, 'r') as file:
                    content = file.read()
            except FileNotFoundError:
                raise FileNotFoundError(f"The file at path '{message}' was not found.")
            except IOError as e:
                raise IOError(f"An error occurred while reading the file: {e}")
        elif hasattr(message, 'read'):
            try:
                content = message.read()
            except IOError as e:
                raise IOError(f"An error occurred while reading the file object: {e}")
        else:
            raise TypeError("message must be a file path, file object, or text")
        initial_prompt = content

        return initial_prompt

    def get_examples(self ):
        pass
    def get_document(self):
        pass
    def get_index(self):
        pass

    def get_sql_prompt(
            self,
            question: str,
            initial_prompt:str = None,
            response_guidelines:str = None,
            question_sql_list:list = None,
            ddl_list:list= None,
            doc_list:list= None,
            **kwargs
    ):
        if initial_prompt is None:
            initial_prompt = f'''
                你是一个{self.dialect}专家. 请帮忙生成一个 SQL 查询来回答这个问题。您的回答应该仅基于给定的上下文，并遵循回答指南和格式说明。
            '''
        if response_guidelines is None:
            response_guidelines = (
            "===回答指南\n"
            "1. 如果提供的上下文足够，请生成一个有效的 SQL 查询，不需要对问题进行任何解释。\n"
            "2. 如果提供的上下文几乎足够，但需要知道特定列中特定字符串的知识，请生成一个中间 SQL 查询以找到该列中不同的字符串。在查询前加上注释说 intermediate_sql \n"
            "3. 如果提供的上下文不充分，请解释为什么不能生成。\n"
            "4. 请使用最相关的表。\n"
            "5. 如果问题之前已经被问过并回答过，请完全按照之前给出的答案重复回答。\n"
            f"6. 确保输出的 SQL 符合 {self.dialect} 的规范且可执行，并且没有语法错误。\n"
            )
        prompt = [self.system_message(initial_prompt + response_guidelines)]




        self.log(self.logger, f"Initial prompt: {prompt}")
        prompt.append(self.user_message(question))

        return prompt


    def add_ddl_to_prompt(self, ddl: str, prompt: str):
        pass

    @abstractmethod
    def system_message(self, message: str) -> any:
        pass

    @abstractmethod
    def user_message(self, message: str) -> any:
        pass

    @abstractmethod
    def assistant_message(self, message: str) -> any:
        pass
