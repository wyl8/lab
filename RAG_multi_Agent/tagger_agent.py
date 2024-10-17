import json
import pickle
import requests
import time


class TaggerAgent:
    def __init__(self,
                 prompt_file = "tagger_prompt.md",
                 qa_file="faq/2024_7_7_岗位_new.json",
                 emb_file="embeddings/2024_7_7_岗位_new.pickle"):
        print("Init TaggerAgent")

        # 加载问题标签分类Agent所需的 QAlist
        with open(qa_file, "r",encoding='utf-8') as f:
            self.qa_data_list = json.load(f)
            print("Loaded data list: ", len(self.qa_data_list))
        
        # 加载 Query所对应的embedding
        with open(emb_file, "rb") as f:
            self.qa_embedding_list = pickle.load(f)
            print("Loaded embedding list: ", len(self.qa_embedding_list))

        with open(prompt_file, "r", encoding='utf-8') as f:
            self.tagger_prompt_template = f.read()

    
    def get_docs(self):
        # 返回QA表和 embedding表
        if self.qa_embedding_list is None or self.qa_data_list is None:
            self.__init__()
        else:
            return self.qa_data_list, self.qa_embedding_list
    
    def tidy_reference_doc_list_for_prompt(self,top_k_docs, top_k_scores):
        # 格式统一改字典了，所以现在doc是字典了
        # {
        #     "ID": "12011271",
        #     "date": "20240118",
        #     "url": "https://andon.woa.com/ticket/detail/?id=12011271&sign=a897429a664ab385764bf68c9d6e822c",
        #     "module": "PMS项目交付",
        #     "tag3": "操作咨询",
        #     "tag4": "项目基本/交付信息问题",
        #     "card_type": "1号卡片",
        #     "ori_query": "你好，咨询下编号为 20220220224639是什么项目怎么关闭交付",
        #     "solution": "关闭交付，可联系以上的PMO人员进行关闭交付的"
        # },
        top_json_list = []
        for score, doc in zip(top_k_scores, top_k_docs):
            tmp_dict = {}
            tmp_dict["basic"] = doc["basic"]
            tmp_dict["L1Tag"] = doc["公司位置"]
            tmp_dict["L2Tag"] = doc["岗位"]
            tmp_dict["L3Tag"] = doc["公司名称"]
            tmp_dict["L4Tag"] = doc["年薪"]
            tmp_dict["similarity"] = round(float(score), 4)
            top_json_list.append(tmp_dict)
        return top_json_list
    
    def make_prompt(self,query,top_k_docs, top_k_scores, top_k = 10):
        #先整理doc
        top_json_list = self.tidy_reference_doc_list_for_prompt(top_k_docs, top_k_scores)
        # 把json数据拼成prompt文本
        top_k = min(top_k, len(top_json_list))
        history_question_info = ''
        for i in range(top_k):
            history_question_info += "- 第{}个相似问题为: 基本信息: {}; 相似度: {}; 公司位置: {}; 岗位: {}; 公司名称: {}; 薪资： {}。\n".format(
                i+1,
                top_json_list[i]["basic"], top_json_list[i]["similarity"],
                top_json_list[i]["L1Tag"], top_json_list[i]["L2Tag"], top_json_list[i]["L3Tag"],
                top_json_list[i]["L4Tag"]  
                )
        
        tagger_prompt = self.tagger_prompt_template.format(
            user_question=query, history_question_info=history_question_info
            )
        
        #print(tagger_prompt)

        return tagger_prompt
 