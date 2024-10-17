import torch
import pdb
import numpy as np
from sentence_transformers import SentenceTransformer, util

class EmbeddingAgent:

    MODEL_PATHs = ['BAAI/bge_m3']

    def __init__(self,model_path = MODEL_PATHs[0]):
        self.model_path = model_path
        self.model = SentenceTransformer("BAAI/bge-m3",device='cuda')
    
    def checkstatus(self):
        # 检查模型是否加载成功
        if self.model is None:
            return False

    def get_embedding(self,sentence):
        # 得到句子的向量表示 384维-L6-v2 L12-v2  768维-sbert-chinese  1024维-bge-m3
        while self.model is None:
            self.__init__()            
        embedding = self.model.encode(sentence)
        return embedding
        #return list(embedding['dense_vecs'])
    
    def get_cosine_sim(self,sentence1,sentence2):
        # 得到两个句子的相似度
        embedding1 = self.get_embedding(sentence1)
        embedding2 = self.get_embedding(sentence2)
        cosine_sim = util.cos_sim(embedding1, embedding2)
        return cosine_sim
    
    def search_top_k(self,query,corpus_embeddings,top_k = 5):
        # 得到相似度最高的top_k个句子
        query_embedding = self.get_embedding(query)
        cosine_scores = util.cos_sim(query_embedding, corpus_embeddings)[0]
        top_k_scores, top_k_indices = torch.topk(cosine_scores, top_k)
        return top_k_scores, top_k_indices


if __name__ == '__main__':
    embedding_agent = EmbeddingAgent()
    corpus = [
        "A man is eating food.",
        "A man is eating a piece of bread.",
        "The girl is carrying a baby.",
        "A man is riding a horse.",
        "A woman is playing violin.",
        "Two men pushed carts through the woods.",
        "A man is riding a white horse on an enclosed ground.",
        "A monkey is playing drums.",
        "A cheetah is running behind its prey.",
        "A man is playing piano",
        "A drum beat comes and a man is playing it"
    ]
    corpus_embeddings = embedding_agent.get_embedding(corpus)
    
    #print(corpus_embeddings.shape)
    corpus_embeddings = np.array(corpus_embeddings)
    #pdb.set_trace()
    #print(type(corpus_embeddings))
    print(corpus_embeddings.shape)
    top_k_scores, top_k_indices = embedding_agent.search_top_k('A man is playing drums.',corpus_embeddings)
    for score, idx in zip(top_k_scores, top_k_indices):
        print(corpus[idx], "(Score: {:.4f})".format(score))
