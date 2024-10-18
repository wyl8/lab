import json
import pickle
import requests
import time
import torch
from transformers import AutoModelForCausalLM

from deepseek_vl.models import VLChatProcessor, MultiModalityCausalLM
from deepseek_vl.utils.io import load_pil_images
from main_pipline import MainPipline


import torch
from embedding_agent import EmbeddingAgent
from tagger_agent import TaggerAgent
from card1_agent import Card1Agent

# Load model directly
# Use a pipeline as a high-level helper
# Load model directly

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
    PIPLINE_OBJ = MainPipline()
    model_path = "deepseek-ai/deepseek-vl-1.3b-chat"
    vl_chat_processor: VLChatProcessor = VLChatProcessor.from_pretrained(model_path)
    tokenizer = vl_chat_processor.tokenizer
    model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16, trust_remote_code=True).cuda()
    
    #code_type = "python"
    user_query = '查看深圳python工程师的岗位'
    attention_res = PIPLINE_OBJ.process_tags(query = user_query, model = model, tokenizer = tokenizer, top_k = 20 )
    print(attention_res)
    
    
    
    exit(0)
    