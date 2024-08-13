from abc import ABC, abstractmethod
from typing import List, Tuple, Union
import logging
from config import base_config
import  os
class Base(ABC):
    def __init__(self, config=None):
        self.config = base_config
        self.dialect = self.config.get("dialect", "SQL")
        self.log_dir = self.config.get("log_dir", "log.log")
        self.logger = self.setup_logger(self.log_dir)
        self.prefix_dir = self.config.get("prefix_dir", "")
        self.index_file = self.config.get("index_file", "")
        self.document_file = self.config.get("document_file", "")
        self.SQL_DDL_file = self.config.get("SQL_DDL_file", "")
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

    def get_rag_sql_prompt(
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

    def get_index_info(self):
        index_file_path = os.path.join(self.prefix_dir, self.index_file)
        if os.path.isfile(index_file_path):
            try:
                with open(index_file_path, "r", encoding="utf-8") as f:
                    index_info = f.read()
            except UnicodeDecodeError as e:
                print(f"解码错误: {e}")
            except Exception as e:
                print(f"读取文件时发生错误: {e}")
        else:
            print(f"文件 {index_file_path} 不存在。")
        return index_info

    def get_ddl_info(self):
        ddl_file_path = os.path.join(self.prefix_dir, self.SQL_DDL_file)
        if os.path.isfile(ddl_file_path):
            try:
                with open(ddl_file_path, "r", encoding="utf-8") as f:
                    ddl_info = f.read()
            except UnicodeDecodeError as e:
                print(f"解码错误: {e}")
            except Exception as e:
                print(f"读取文件时发生错误: {e}")
        else:
            print(f"文件 {ddl_file_path} 不存在。")
        return ddl_info

    def get_example_info(self):
        return None
    def get_semantic_prompt(self, question, initial_semantic_prompt: str = None):
        if initial_semantic_prompt is None:
            initial_semantic_prompt = '''
            # 角色:语义分析专家
                您的回答应该仅基于给定的上下文，并遵循回答指南和格式说明
            # 工作内容：
                1. 根据用户的问题question，进行语义分析，从question中提取出时间，科室，指标三个元素，其中任意一项均不能为空，科室可以为全部科室，所有科室
            ## 说明
                1. 如果时间为**年，则您必须主动将其转换为**年1月1日至12月31日, 
                2. 如果时间为**上半年, 则您必须主动将其转换为**年1月1日至6月30日,
                3. 以此类推，如果包含季度等潜在时间信息，也需要您主动将其转换为具体时间段
            ## 规则
                如果能够成功分解，则返回格式为{"Done": "True", "question":question ,"result": {"时间": "", "科室": "", "指标": ""}}
                如果不能够成功分解，则提示用户如下信息 text"已经提取出的信息为：**，但您的问题中缺少**信息，请补充完整"，并将其存入result中，让用户输入，
                返回格式为{"Done": "True", "question":question ,"result": "text"}
            '''
            semantic_prompt = [self.system_message(initial_semantic_prompt), self.user_message(question)]
            return semantic_prompt



    def get_sql_prompt(self,question,thingking):
        ddl_info = self.get_ddl_info()
        index_info = self.get_index_info()
        example_info = self.get_example_info()
        sql_prompt = f'''
            # 角色: {self.dialect}专家
            请结合解决问题专家的建议，帮忙生成一个SQL查询来回答用户的question。您的回答应该仅基于给定的上下文，并遵循回答指南和格式说明。
            ## 数据库的结构：
                {ddl_info}
            ## 指标计算公式：
                {index_info}
            ## 参考示例：
                {example_info}
            ## 解决问题专家的建议
                {thingking}
            ## 用户问题：
                {question}
            # 回答:
                根据以上信息，直接生成回答question的SQL语句, 请确保输出的 SQL 符合 {self.dialect} 的规范且可执行，并且没有语法错误。
        '''

    def get_thinking_prompt(self, question, semantic:str = None):
        ddl_info = self.get_ddl_info()
        index_info = self.get_index_info()
        example_info = self.get_example_info()
        thinking_initial_prompt = f'''
        # 角色:思考专家    
            1. 您的回答应该仅基于给定的上下文，并遵循回答指南和格式说明
            2. 您的回答将提供思路，以指导最终的SQL语句生成
        # 信息说明: 
            ## 1. ddl_info: 该部分包含数据库的表结构信息
                {ddl_info}
            ## 2. index_info: 该部分包含指标名称和指标的计算公式或过程
                {index_info}
            ## 3. example_info:该部分为示例信息，用于帮助用户理解问题
                {example_info}
        # 回答指南：
            1. 根据用户的问题question和semantic，借鉴example_info， 从ddl_info,index_info中提取出最相关的信息, 并以此说明您解决此问题的思路，
                思路应尽量简洁,如果有复杂问题，可将问题进行分解。
               思路只需包含以下内容: 使用哪些表，及列[列名1，列名2,...]，计算过程，涉及的操作
                输出格式为:{{"Done":"True", "res":""}}
            2. 如果无法从ddl_info和index_info中提取出最相关的信息，请说明原因，
                输出格式为:{{"Done":"False", "res":""}}
        '''
        thinking_prompt = [self.system_message(thinking_initial_prompt), self.user_message(question+semantic)]
        return thinking_prompt



        
        
        
        
        
        
    def add_ddl_to_prompt(self, ddl: str, prompt: str):
        pass
    def add_index_to_prompt(self, index: str, prompt: str):
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
