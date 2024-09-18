import json
import pickle
import requests
import time

from embedding_agent import EmbeddingAgent
from tagger_agent import TaggerAgent
from card1_agent import Card1Agent

from transformers import AutoTokenizer, AutoModelForCausalLM


def load_json_data(file_name):
    with open(file_name, 'r') as f:
        data = json.load(f)
    print("load_json_data: ",len(data))
    return data


if __name__ == "__main__":
    embedding_agent = EmbeddingAgent(model_path = "/BAAI/bge-m3")
    tagger_agent = TaggerAgent(prompt_file = "tagger_prompt.md",
                                        qa_file = "faq/2024_7_7_岗位_new.json",
                                        emb_file = "embeddings/HQA_embedding_0618_list_bge-m3.pickle")
    card1_agent = Card1Agent(prompt_file = "card1_prompt.md")
    """
    这个是本地运行的，需要一个model和一个tokenizer
    """
    model_path = "./model/deepseek-aideepseek-coder-7b-instruct-v1.5"
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(model_path, 
                                                 torch_dtype=torch.float16, 
                                                 trust_remote_code=True).cuda()
    
    code_type = "python"
    user_query = '查看深圳工程师的岗位'
    attention_res = process_tags(query = user_query, model, tokenizer, top_k = 10 )
    print(attention_res)
    
    
    
    exit(0)
    