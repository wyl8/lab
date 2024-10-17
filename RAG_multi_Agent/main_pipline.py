import json
import pickle
import requests
import time

from embedding_agent import EmbeddingAgent
from tagger_agent import TaggerAgent
from card1_agent import Card1Agent

class MainPipline:
    def __init__(self):
        self.embedding_agent = EmbeddingAgent(model_path = "BAAI/bge-m3")
        self.tagger_agent = TaggerAgent(prompt_file = "tagger_prompt.md",
                                        qa_file = "faq/2024_7_7_岗位_new.json",
                                        emb_file = "embeddings/2024_7_7_岗位_new.pickle")
        self.card1_agent = Card1Agent(prompt_file = "card1_prompt.md")

    def checkstatus(self):
        if self.embedding_agent.checkstatus() == False:
            self.embedding_agent = EmbeddingAgent()
            return True

    
    def find_reference_docs(self, query, qa_data_list, qa_embedding_list, top_k=10):
        top_k_scores, top_k_indices = self.embedding_agent.search_top_k(query, qa_embedding_list, top_k)
        top_k_docs = []
        for idx in top_k_indices:
            top_k_docs.append(qa_data_list[idx])
        return top_k_docs, top_k_scores
    

    def get_llm_response(self,prompt):
        """
        请求deepseek-coder-7b-instruct-v1.5 + dummy 模型
        curl --location '42.192.32.62:8005/v1/chat/completions' \
        --header 'Content-Type: application/json' \
        --data '{
            "model": "codewise-chat",
            "stream": false,
            "temperature": 0,
            "messages": [
            {
                "role": "user",
                "content": "Who are you"
            }
            ]
        }'
        """
        model_url = "http://42.192.32.62:8005/v1/chat/completions"
        headers = {'Content-Type': 'application/json'}
        data = {
                "model": "codewise-chat",
                "stream": False,
                "temperature": 0,
                "use_beam_search": True,
                "best_of": 5,
                "n": 1, 
                "messages": 
                [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
        }
        try:
            response = requests.post(model_url, headers=headers, data=json.dumps(data))
            res_json = response.json()
            status_code = response.status_code
            if status_code != 200:
                print("请求失败，状态码: ", status_code)
                res_json = {'error': '请求失败'}
        except Exception as e:
            print("请求失败，原因: ", e)
            res_json = {'error': '请求失败'}
            
        return res_json
    
    def get_llm_response_local(self, prompt, model, tokenizer):
        """
        这里是本地调用LLM使用的，测试子健的模型
        """
        result = None
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        print('### Input: ', tokenizer.decode(inputs.input_ids[0], skip_special_tokens=False))

        outputs = model.language_model.generate(**inputs, max_new_tokens=2048, do_sample=False, top_k=50, top_p=0.95, num_return_sequences=1, eos_token_id=tokenizer.eos_token_id) # eos_token_id=100015 | 32014 | 32021 | 49155)
        result = tokenizer.decode(outputs[0][len(inputs.input_ids[0]):], skip_special_tokens=True)
        print('### Output: ', result)

        return result

    def extract_result(self, res_json):
        """
        从大模型返回结果中提取出分类标签，大模型的结果主要有以下几种
        1、直接返回json格式字典，例如 { "一级标签": "经平-操作效率&体验", "二级标签": "PES测算管理", "三级标签": "操作咨询", "四级标签": "测算审批流程操作咨询" }
        2、使用markdown格式返回，例如    ```json
                                        {
                                            "一级标签": "经平-业务规则&流程",
                                            "二级标签": "商机&报价领域",
                                            "三级标签": "业务流程&规则疑问",
                                            "四级标签": "报价测算与审批"
                                        }
                                        ```
        3、结果比较随意，例如：返回的结果为： { "一级标签": "经平-业务规则&流程", "二级标签": "商机&报价领域",
                                "三级标签": "业务流程&规则疑问",
                                "四级标签": "报价测算与审批" }
        """
        # 为了处理以上结果，统一寻找字典的{}格式，并进行字典转换，如果失败，则返回原文吧
        find_flag = False
        start_index = 0
        end_index = len(res_json)
        res_dict = {}
        while not find_flag :
            try:
                start_index = res_json.index("{", start_index)
                end_index = res_json.index("}", start_index+1)
                json_str = res_json[start_index:end_index+1]
            except:
                # 到这里就是找不到匹配的{}对了,退出循环
                break
            
            # 为了简化判断分成两个try 和 except吧，上面的寻找字符串，这里做转换
            try:
                res_dict = json.loads(json_str)
                find_keys = res_dict.keys()
                if len(find_keys) > 0:
                    find_flag = True
                    break
                else:
                    start_index = end_index + 1
                    continue
            except:
                # 这里是转换成字典失败了，更新index，继续寻找,至少向前走一步，如果下次没找{}到则直接推出了
                start_index = max(start_index, end_index)
                start_index += 1
                continue
        # 没找到结果
        if not find_flag:
            res_dict = {"error": "未找到结果"}
            print("未找到结果")

        return res_dict

    
    def process_tags(self,query, model, tokenizer, top_k = 10):
        """
        这里提取分类信息，为知识库提供更多的参考
        """
        tagger_qa_data_list, tagger_qa_embedding_list = self.tagger_agent.get_docs()
        top_k_docs, top_k_scores = self.find_reference_docs(query, tagger_qa_data_list, tagger_qa_embedding_list, top_k)
        tagger_prompt = self.tagger_agent.make_prompt(query, top_k_docs, top_k_scores, top_k)
        #print("***********************************",tagger_prompt,"***********************************************")
        res_json = self.get_llm_response_local(tagger_prompt, model, tokenizer)
        """
        if "error" in res_json.keys() and res_json["error"] == "请求失败":
            return {"error": "请求失败"}
        """   
        #res_content = res_json['choices'][0]['message']['content']
        #extract_result = self.extract_result(res_content)
        extract_result = []
        return extract_result
    
    def process_card1(self,query):
        """
        提取卡片1中的角色和订单号
        """
        card1_prompt = self.card1_agent.make_prompt(query)
        res_json = self.get_llm_response(card1_prompt)
        if "error" in res_json.keys() and res_json["error"] == "请求失败":
            return {"error": "请求失败"}
        res_content = res_json['choices'][0]['message']['content']
        extract_result = self.extract_result(res_content)

        return extract_result





if __name__ == "__main__":
    agent_pipline = MainPipline()
    print("Finish Init ")
    