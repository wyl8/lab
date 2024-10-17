# 基于RAG的岗位查询
基于RAG的岗位查询
简单来说是利用文档检索加大模型的推理能力来识别用户问题的意图。

## 第1步 相似问题匹配--知识获取天花板
这里第1步主要做下面的工作
- 1、建立indexing库：这里使用理解检索里面介绍的模型先把参考资料（我从招聘网站爬的一部分计算机岗位的招聘信息）进行doc2vec，并把参考文档的embeddings保存起来
- 2、Query的vec化并计算相似度：用同样的模型对用户问题进行doc2vec，并利用的得到的embedding去和参考文档的embeddings逐一计算相似度，并返回最接近的Top N个（实验先取10个）文档编号
- 3、取出相关文档：取出这Top N个文档编号对应的实际信息
为什么说这里是天花板呢：很直观的解释就是，如果草考文档里没有正确的信息，那么后面大模型再怎么厉害也不可能找到或者推理出正确的答案。

## 第2步 大模型推理--确定模型推理能力
这里第2步主要做下面的工作
- 1 拼接调用LLM所需的prompt，其中包含 a)第1步中的到的参考文档作为Context的一部分； b) 编写调用大模型所需的指令，就是问题后那行 Please answer the above questions based on the follwing information:
- 2 使用1中的prompt调用LLM得到结果

# 模型选择说明
这里试验过GPT4、混元、还有Deepseek这三个，初步定性分析效果相差不大。基本都是检索相关度较高时到三级标签都是正确的。
特别在上面文档中进行了利用模型自省能力的实验，其实就是模拟Agent系统的自我检查，所有模型都出现摇摆不定的情况，而且因为暂时没有较好的分类辩伪方法，自省能力暂时无法发挥效果。

综合考虑，这里选择自己部署的Deepseek，主要有以下原因
- 就在该问题表现上与GPT4基本相当
- 参数更加可控，开启beam——search后效果有明显提升
- 方便后期有积累数据时进行SFT调优

# Demo说明
Demo为了演示方便用python搭建了一个bottle的服务，跑起了全部流程，不过只是适用，没有负载均衡和优化这些
- 其中doc2vec用了智源的最新模型BGE-M3，用huggingface 的 SentenceTransformer 库调用，每个实例大概占用3GB显存
- 大模型部署了一个deepseek-coder-1.3b-instruct-v1.5（7b需要的显存太大了），只有一个实例，也没有开TP加速等
- 每个问题识别大概需要5-6秒的时间


```Text
.
|-- embeddings                    # 历史问题正文部分的doc2vec，数组，pickle存储
|-- faq                           # 历史问题分类的文本格式，字典数组，index与embeddings一一对应
|-- card1_agent.py                # 第一类卡片：项目角色查询agent
|-- card1_prompt.md               # 第一类卡片对应的prompt
|-- embedding_agent.py            # 多有Embedding操作封装在这里了 
|-- main_pipline.py               # 串联各种Agent的主控逻辑
|-- o_rag_service                 # uwsgi的软链接，改个名字是为了好管理实例(软链操作请见start_service.sh中，需要自己安装uwsgi并链接过来)
|-- o_service.py                  # 服务器逻辑
|-- process_new_data.py           # 加工embeddings和faq的数据的脚本
|-- start_service.sh              # 服务启动脚本
|-- tagger_agent.py               # 资讯类问题分类Agent
|-- tagger_prompt.md              # 资讯类问题分类agent对应的prompt
|-- tagger_service.log            # 请求具体内容日志，先记录全部信息
|-- uwsgi_offical.log             # 服务器响应日志
```
## 可以直接运行local.py尝试一下（将模型部署到workspace/本地）