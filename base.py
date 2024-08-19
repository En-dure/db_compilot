import json
import threading
from abc import ABC, abstractmethod
from typing import List, Tuple, Union
import logging
from exceptions import DependencyError, ValidationError, ImproperlyConfigured
from config import base_config
import os
import pandas as pd
from decimal import Decimal
import  time
import sys
import select
class Base(ABC):
    def __init__(self, config=None):
        self.config = base_config
        self.dialect = self.config.get("dialect", "SQL")
        self.log_dir = self.config.get("log_dir", "log.log")
        self.logger = self.setup_logger(self.log_dir)
        self.prefix_dir = self.config.get("prefix_dir", "")
        self.index_file = self.config.get("index_file", "")
        self.document_file = self.config.get("document_file", "")
        self.example_file = self.config.get("example_file", "")
        self.SQL_DDL_file = self.config.get("SQL_DDL_file", "")
        self.run_sql_is_set = False
        self.relation_file = self.config.get("relation_file", "")
        self.get_extra_info()
        self.times = 1
        self.semantic_flag = 1
        self.MAX_TIMES = self.config.get("MAX_TIMES", 10)
        self.MAX_SQL_ATTEMPT = self.config.get("MAX_SQL_ATTEMPT", 3)
        self.AUTO_ADD_EXAMPLES = self.config.get("AUTO_ADD_EXAMPLES", False)

    def get_extra_info(self):
        self.ddl_info = self.get_ddl_info()
        self.index_info = self.get_index_info()
        self.example_info = self.get_example_info()
        self.document_info = self.get_document_info()
        self.relation_info = self.get_relation_info()

    def setup_logger(self, log_file: str, name: str = __name__, level: str = "INFO"):
        logger = logging.getLogger(name)
        if not logger.hasHandlers():
            logger.setLevel(level)
            file_handler = logging.FileHandler(log_file)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s ----- %(message)s')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        return logger

    def log(self, logger, message: str, title: str = "Info"):
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

    def get_document_info(self):
        document_file_path = os.path.join(self.prefix_dir, self.document_file)
        if os.path.isfile(document_file_path):
            try:
                with open(document_file_path, "r", encoding="utf-8") as f:
                    document_info = f.read()
            except UnicodeDecodeError as e:
                print(f"解码错误: {e}")
            except Exception as e:
                print(f"读取文件时发生错误: {e}")
        else:
            print(f"文件 {document_file_path} 不存在。")
        return document_info

    def get_example_info(self):
        example_file_path = os.path.join(self.prefix_dir, self.example_file)
        if os.path.isfile(example_file_path):
            try:
                with open(example_file_path, "r", encoding="utf-8") as f:
                    example_info = f.read()
            except UnicodeDecodeError as e:
                print(f"解码错误: {e}")
            except Exception as e:
                print(f"读取文件时发生错误: {e}")
        else:
            print(f"文件 {example_file_path} 不存在。")
        return example_info

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

    def get_relation_info(self):
        relation_file_path = os.path.join(self.prefix_dir, self.relation_file)
        if os.path.isfile(relation_file_path):
            try:
                with open(relation_file_path, "r", encoding="utf-8") as f:
                    relation_info = f.read()
            except UnicodeDecodeError as e:
                print(f"解码错误: {e}")
            except Exception as e:
                print(f"读取文件时发生错误: {e}")
        else:
            print(f"文件 {relation_file_path} 不存在。")
        return relation_info

    def get_semantic_prompt(self, question, initial_semantic_prompt: str = None, reget_info:str = ''):
        if initial_semantic_prompt is None:
            initial_semantic_prompt = f'''
            # 角色:语义分析专家
                你的回答应该仅基于给定的上下文，并遵循回答指南和格式说明
            ## 工作内容：
                1. 根据用户的完整问题，进行语义分析，从中提取出时间，科室，指标三个元素，其中任意一项均不能为空。
            ##  document_info:该部分为补充信息，必须重点关注
                {self.document_info}
            ##  relation_info: 该部分为科室的关系树，用户帮助你梳理科室之间的关系
                {self.relation_info}
            ## 关键说明
                1. 如果时间为**年，则您必须主动将其转换为**年1月1日至12月31日, 
                2. 以此类推，如果包含季度等潜在时间信息，你需要主动将其转换为具体时间段
                3. 如果用户问全院，则为全部科室。
            ## 回答指南和格式说明
                1. 你必须将用户原始question和reget_info重新梳理组合作为最终的question。reget_info会包含用户的补充信息，或特殊要求。
                2. 如果能够成功分解，则返回格式为{{"Done": "True", "question":question ,"result": {{"时间": "", "科室": "", "指标": ""}}}}
                3. 如果不能够成功分解，则提示用户补充相关信息，将你的提示存入result中，等待用户输入,
                返回格式为{{"Done": "True", "question":question ,"result": ""}}
                4. 不能成功分解后，用户会补充信息reget_info, 将此信息与原始question结合作为完整用户提问，重新分解，循环此过程，直到你有足够多的信息，可以进行语义分析。
            '''

            semantic_prompt = [self.system_message(initial_semantic_prompt), self.user_message(question + reget_info)]
            return semantic_prompt

    def get_thinking_prompt(self, question, semantic: str = None):

        thinking_initial_prompt = f'''
        # 角色:思考专家    
            1. 你的回答应该仅基于给定的上下文，并遵循回答指南和格式说明
            2. 你的回答将提供思路，以指导最终的SQL语句生成
            3. 如果example_info中有相同的问题，你必须在思路中直接说明参考的例子
        # 信息说明: 
            ## 1. ddl_info: 该部分包含数据库的表结构信息
                {self.ddl_info}
            ## 2. index_info: 该部分包含指标名称和指标的计算公式或过程
                {self.index_info}
            ## 3. example_info:该部分为示例信息，用于帮助用户理解问题
                {self.example_info}
            ## 4. document_info:该部分为补充信息，必须重点关注
                {self.document_info}
            ## 5. relation_info: 该部分为科室的关系树，用户帮助你梳理科室之间的关系
                {self.relation_info}
           
        # 回答指南：
            1. 根据用户的问题question和semantic，借鉴example_info， 从ddl_info,index_info,document_info，relation_info中提取出最相关的信息, 并以此说明你解决此问题的思路，
                思路应尽量简洁,如果有复杂问题，可将问题进行分解。
            2.  指标的计算必须严格按照index_info里面的计算公式计算，如果指标涉及到多重计算，必须说明。否则，将对你进行惩罚。
            3. 如果用户的问题中指明了具体科室，那你必须根据document_info中的信息，根据确定科室流程，在relation_info中挑选出具体的科室
            4. 思路只需包含以下内容: 使用哪些表，及列[列名1，列名2,...]，从index_info中找到的计算公式，以及基于这些信息，用到的函数，你的思路。
                其中列名必须为数据表的包含的字段，着重考虑是否需要使用聚合函数，SUM等函数。
                你必须说明提取的具体是哪些科室，及其从哪个字段提取，以及提取的列名。
                输出格式为:{{"Done":"True", "res":""}} res的内容需转化为json格式，因此不要有非法换行符等内容。
            5. 如果无法从ddl_info和index_info中提取出最相关的信息，说明原因，
                输出格式为:{{"Done":"False", "res":""}}
            6. 
        '''
        thinking_prompt = [self.system_message(thinking_initial_prompt), self.user_message(question + semantic)]
        return thinking_prompt

    def get_sql_prompt(self, question, thingking, error: str = None):

        sql_prompt = f'''
            # 角色: {self.dialect}专家
            结合解决问题专家的建议，帮忙生成一个SQL查询来回答用户的question。你的回答应该仅基于给定的上下文，并遵循回答指南和格式说明。
            # 特殊说明
            如果参考示例中有相同的问题，直接返回SQL语句,不要做任何修改。
            ## 数据库的结构：
                {self.ddl_info}
            ## 指标计算公式：
                {self.index_info}
            ## 参考示例：
                {self.example_info}
            ## 补充信息:
                {self.document_info}
            ## 关系树:
                {self.relation_info}
            ## 解决问题专家的建议
                {thingking}
            ## 用户问题：
                {question}
            ##  运行SQL错误信息
                {error}
            # 回答:
                1.必须包含 question中的时间, 科室，指标三个元素
                2.根据以上信息，直接生成回答question的SQL语句, 不要有任何额外信息，必须确保输出的 SQL 符合 {self.dialect} 的规范且可执行，并且没有语法错误。
                不要有任何非法符号。
                3. 尽量使用简单的SQL语句，需要考虑是否正确使用SUM函数
                4. 如果参考示例中有相同的问题，直接返回SQL语句
                5. 如果有错误信息，根据错误信息，重新生成SQL语句
        '''
        thinking_prompt = [self.system_message(sql_prompt), self.user_message(question)]
        return thinking_prompt

    def get_reflection_prompt(self, question: str, thinking: str, SQL: str):

        reflection_prompt = f'''
            # 角色: {self.dialect}顶级专家
            1. 结合解决问题专家的建议和 {self.dialect}专家的回答和用户的question, 检查{self.dialect}专家的SQL回答是否能够解决用户的问题
            2. 你的回答应该仅基于给定的上下文，并遵循回答指南和格式说明。
            ## 数据库的结构：
                {self.ddl_info}
            ## 指标计算公式：
                {self.index_info}
            ## 参考示例：
                {self.example_info}
            ## 补充信息:
                {self.document_info}
            ## 关系树:
                {self.relation_info}
            ## 解决问题专家的建议:
                {thinking}
            ## 用户问题：
                {question}
            ## {self.dialect}专家的回答
                {SQL}
            # 回答
                根据以上信息:
                1. 如果SQL语句没有错误或要修改的内容, 直接返回SQL语句, 不要有任何额外信息，不要有任何非法符号
                2. 如果SQL语句有错误或要修改的内容, 直接返回修改后的SQL语句, 不要有任何额外信息
                3. 必须确保输出的 SQL 符合 {self.dialect} 的规范且可执行，并且没有语法错误。
                4. 必须保证SQL语句中包含了question中的 时间, 指标，科室三个元素
        '''
        thinking_prompt = [self.system_message(reflection_prompt), self.user_message(question)]
        return thinking_prompt

    def get_final_prompt(self, question, result):
        final_prompt = f'''
            # 角色: 数据分析师
             你的回答应该仅基于给定的上下文，并遵循回答指南和格式说明。
            ## 主要工作:
            1. 根据用户的question和最终查询结果，给用户一个简短的回答。
            ## 回答:
            1. 选择合适的数量单位回答,超过十万，用万为单位回答。超过亿，用亿为单位回答。
            2. 涉及到比例的，转换为百分比回答，保留两位小数
            ## 用户问题:
                {question}
            '''
        final_prompt = [self.system_message(final_prompt), self.user_message(result)]
        return final_prompt

    def connect_to_mysql(
            self,
            host: str = None,
            dbname: str = None,
            user: str = None,
            password: str = None,
            port: int = None,
            **kwargs
    ):
        try:
            import pymysql.cursors
        except ImportError:
            raise DependencyError(
                "You need to install required dependencies to execute this method,"
                " run command: \npip install PyMySQL"
            )
        if not host:
            host = os.getenv("HOST")

        if not host:
            raise ImproperlyConfigured("Please set your MySQL host")

        if not dbname:
            dbname = os.getenv("DATABASE")

        if not dbname:
            raise ImproperlyConfigured("Please set your MySQL database")

        if not user:
            user = os.getenv("USER")

        if not user:
            raise ImproperlyConfigured("Please set your MySQL user")

        if not password:
            password = os.getenv("PASSWORD")

        if not password:
            raise ImproperlyConfigured("Please set your MySQL password")

        if not port:
            port = os.getenv("PORT")

        if not port:
            raise ImproperlyConfigured("Please set your MySQL port")

        conn = None

        try:
            conn = pymysql.connect(
                host=host,
                user=user,
                password=password,
                database=dbname,
                port=port,
                cursorclass=pymysql.cursors.DictCursor,
                **kwargs
            )
        except pymysql.Error as e:
            raise ValidationError(e)

        def run_sql_mysql(sql: str):
            if conn:
                try:
                    conn.ping(reconnect=True)
                    cs = conn.cursor()
                    cs.execute(sql)
                    results = cs.fetchall()

                    # Create a pandas dataframe from the results
                    df = pd.DataFrame(
                        results, columns=[desc[0] for desc in cs.description]
                    )
                    return True, df

                except pymysql.Error as e:
                    conn.rollback()
                    # raise ValidationError(e)
                    return False, e
                except Exception as e:
                    conn.rollback()
                    return False, e
        self.run_sql_is_set = True
        self.run_sql = run_sql_mysql




    def ask(self, question):
        reget_info = ''
        while self.times <= self.MAX_TIMES:
            semantic_prompt = self.get_semantic_prompt(question, reget_info=reget_info)
            semantic = self.submit_semantic_prompt(semantic_prompt)
            semantic_result = json.loads(semantic)
            if semantic_result["Done"] == "True":
                question = str(semantic_result["question"])
                semantic_result = str(semantic_result["result"])
                print("semantic_result", semantic_result)
            else:
                print(semantic_result["result"])
                reget_info = input("请补充相关信息:")
                self.times += 1
                continue
            self.log(self.logger, "question:" + question)
            self.log(self.logger, "semantic:" + semantic)
            thinking = self.get_thinking_prompt(question, semantic_result)
            thinking_result = self.submit_thinking_prompt(thinking)
            self.log(self.logger, "thinking:" + thinking_result)
            try:
                thinking_result = json.loads(thinking_result)
            except Exception as e:
                print(e)
                self.times += 1
                continue
            if thinking_result["Done"] == "False":
                print("thinking_result:", thinking_result["res"])
                self.times += 1
            else:
                thinking_result = thinking_result["res"]
                print("thinking_result:", thinking_result)
            sql_attempt = 1
            error = ''
            while sql_attempt <= self.MAX_SQL_ATTEMPT:
                sql_prompt = self.get_sql_prompt(question, thinking_result, error)
                initial_sql = self.submit_prompt(sql_prompt)
                print("initial_sql:", initial_sql)

                reflection_prompt = self.get_reflection_prompt(question, thinking_result, initial_sql)
                reflection = self.submit_reflection_prompt(reflection_prompt)
                print("reflection:", reflection)

                y_or_n, run_sql_result,  = self.run_sql(reflection)
                if not y_or_n:
                    error = run_sql_result
                    self.log(self.logger, "SQL:" + reflection)
                    self.log(self.logger, "SQL error:" + str(error))
                    print(f"第{sql_attempt} 次运行SQL失败， 进行下一次尝试")
                    sql_attempt += 1
                    continue
                break
            if not isinstance(run_sql_result, pd.DataFrame):
                if not run_sql_result:
                    self.times += 1
                    continue
            self.log(self.logger, "initial_sql:" + initial_sql)
            self.log(self.logger, "reflection:" + reflection)
            print("result:", run_sql_result)
            sql_result = run_sql_result.to_dict()
            converted_dict = {key: {k: float(v) if isinstance(v, Decimal) else v for k, v in value.items()} for
                              key, value in sql_result.items()}
            sql_result = json.dumps(converted_dict, ensure_ascii=False)
            self.log(self.logger, "sql_result:" + sql_result)
            final_prompt = self.get_final_prompt(question, sql_result)
            result = self.submit_final_prompt(final_prompt)
            self.log(self.logger, "查询结果:" + result)
            print("查询结果:", result)
            self.times = 1
            # self.auto_add_examples(question, reflection, auto=self.AUTO_ADD_EXAMPLES)
            break
    def auto_add_examples(self, question, sql, auto = False):
        if auto:
            self.add_example(question, sql)
            return "Auto Added"

        add_or_no = input("是否添加到样例中？, 添加请输入 y，不添加请输入 n\n请输入您的选择：")
        print("您的选择是:", add_or_no)
        if add_or_no == "y":
            self.add_example(question, sql)
        elif add_or_no == "n":
            pass
        else:
            print("无效的输入，请输入 'y' 或 'n'。")

    def add_example(self, question, sql, example_file = None):
        if not example_file:
            example_file = self.example_file
        new_example = {
            "question": question,
            "SQL": sql
        }
        # 读取现有的 JSON 文件
        with open(example_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
        # 将新例子追加到 examples 数组
        if 'examples' not in data:
            data['examples'] = []
        data['examples'].append(new_example)
        # 将更新后的数据写回 JSON 文件
        with open('addition/example.json', 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

    def add_ddl_to_prompt(self, ddl: str, prompt: str):
        pass

    def add_index_to_prompt(self, index: str, prompt: str):
        pass

    @abstractmethod
    def submit_final_prompt(self, final_prompt: List):
        pass

    @abstractmethod
    def submit_semantic_prompt(self, semantic_prompt: List):
        pass

    @abstractmethod
    def submit_thinking_prompt(self, thinking: List):
        pass

    @abstractmethod
    def submit_prompt(self, prompt: List):
        pass

    @abstractmethod
    def submit_reflection_prompt(self, question: List, ):
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
