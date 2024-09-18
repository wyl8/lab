# 基于RAG的客服用户问题识别
基于RAG的客服用户问题识别 可以看[这个详细介绍](https://doc.weixin.qq.com/doc/w3_APIA0QZ_ACc0GkzmZKzRLGC00P9dM?scode=AJEAIQdfAAoS3JkrLFAPIA0QZ_ACc)
简单来说是利用文档检索加大模型的推理能力来识别用户问题的意图。

## 第1步 相似问题匹配--知识获取天花板
这里第1步主要做下面的工作
- 1、建立indexing库：这里使用理解检索里面介绍的模型先把参考资料进行doc2vec，并把参考文档的embeddings保存起来
- 2、Query的vec化并计算相似度：用同样的模型对用户问题进行doc2vec，并利用的得到的embedding去和参考文档的embeddings逐一计算相似度，并返回最接近的Top N个（实验先取10个）文档编号
- 3、取出相关文档：取出这Top N个文档编号对应的实际信息
为什么说这里是天花板呢：很直观的解释就是，如果草考文档里没有正确的信息，那么后面大模型再怎么厉害也不可能找到或者推理出正确的答案。

## 第2步 大模型推理--确定模型推理能力
这里第2步主要做下面的工作
- 1 拼接调用LLM所需的prompt，其中包含 a)第1步中的到的参考文档作为Context的一部分，就是图中的chunk1-3； b) 编写调用大模型所需的指令，就是问题后那行 Please answer the above questions based on the follwing information:
- 2 使用1中的prompt调用LLM得到结果

# 模型选择说明
这里试验过GPT4、混元、还有Deepseek这三个，初步定性分析效果相差不大。基本都是检索相关度较高时到三级标签都是正确的[这个详细介绍](https://doc.weixin.qq.com/doc/w3_APIA0QZ_ACc0GkzmZKzRLGC00P9dM?scode=AJEAIQdfAAoS3JkrLFAPIA0QZ_ACc)。
特别在上面文档中进行了利用模型自省能力的实验，其实就是模拟Agent系统的自我检查，所有模型都出现摇摆不定的情况，说明模型本身并未有确定的小O经管问题分类能力。而且因为暂时没有较好的分类辩伪方法，自省能力暂时无法发挥效果。

综合考虑，这里选择自己部署的Deepseek，主要有以下原因
- 就在该问题表现上与GPT4基本相当
- 参数更加可控，开启beam——search后效果有明显提升
- 方便后期有积累数据时进行SFT调优

# Demo说明
Demo为了演示方便用python搭建了一个bottle的服务，跑起了全部流程，不过只是适用，没有负载均衡和优化这些
- 其中doc2vec用了智源的最新模型BGE-M3，用hugging face 的 SentenceTransformer 库调用，每个实例大概占用3GB显存这样
- 向量检索因为目前只从5k个1k维度检索，直接用了SentenceTransformer来计算cosin相似度，速度还可以的
- 大模型由后台同学帮忙部署了一个deepseek-coder-7b-instruct-v1.5，只有一个实例，也没有开TP加速等
- 每个问题识别大概需要5-6秒的时间

## 卡片类型结果
3.0这里主要按照新的标签体系开发的，把卡片内容归结到了一级标签和二级标签中：一级标签：工具类型，二级标签：一个是如果你可以查出来项目ID，那就是InquireRole。查不出来就InquireRoleExcludeID
```Shell
curl -H"Content-Type: text/json" -d'{"user_query": "辛苦帮忙查询确认一下编号20220516240001这个项目的项目经理"}'  'http://9.134.172.218:26666/query_tagger'
```
可以通过一级标签区分卡片类型，二级标签区分是否有项目编号
```json
{"一级标签": "工具类型", "二级标签": "InquireRole", "三级标签": "操作咨询", "四级标签": "项目成员问题", "card_info": {"项目编号": "20220516243495", "项目角色": "pm"}}
```
对上面例子进行一下修改，去掉项目编号等信息
```Shell
curl -H"Content-Type: text/json" -d'{"user_query": "辛苦帮忙查询确认一下数字经济产业基地项目的项目经理"}'  'http://9.134.172.218:26666/query_tagger'
```
可以通过一级标签区分卡片类型，二级标签这里就没有项目标号的含义
```json
{"一级标签": "工具类型", "二级标签": "InquireRoleExcludeID", "三级标签": "操作咨询", "四级标签": "项目成员问题", "card_info": {"项目编号": "未找到", "项目角色": "pm"}}
```

## 咨询类型结果
```Shell
curl -H"Content-Type: text/json" -d'{"user_query": "代理商想主动解绑代客 这个流程是？"}'  'http://9.134.172.218:26666/query_tagger'
```
会得到下面的结果为预测的1-4级标签，大模型的解释信息已经过滤掉了。找经管同学确认过解释的质量，时对时错，主要依赖检索的质量，说明在检索信息靠谱时，大模型的推理有时是正确的
```json
{"一级标签": "客户经营平台产品中心", "二级标签": "合作伙伴控制台", "三级标签": "代客管理-代客解绑", "四级标签": "咨询类"}
```

# 文件结构
相比于1.0版本做了较大的改动

```Text
.
|-- embeddings                    # 历史问题正文部分的doc2vec，数组，pickle存储
|-- faq                           # 历史问题分类的文本格式，字典数组，index与embeddings一一对应
|-- card1_agent.py                # 第一类卡片：项目角色查询agent
|-- card1_prompt.md               # 第一类卡片对应的prompt
|-- embedding_agent.py            # 多有Embedding操作封装在这里了 
|-- main_pipline.py               # 串联各种Agent的主控逻辑
|-- New_tags_20240618.txt         # 5条样例数据
|-- o_rag_service                 # uwsgi的软链接，改个名字是为了好管理实例(软链操作请见start_service.sh中，需要自己安装uwsgi并链接过来)
|-- o_service.py                  # 服务器逻辑
|-- process_new_data.py           # 加工embeddings和faq的数据的脚本
|-- start_service.sh              # 服务启动脚本
|-- tagger_agent.py               # 资讯类问题分类Agent，1.0版本的功能
|-- tagger_prompt.md              # 资讯类问题分类agent对应的prompt
|-- tagger_service.log            # 请求具体内容日志，先记录全部信息
|-- uwsgi_offical.log             # 服务器响应日志
```
