# 基于多Agent的单测代码生成
这里主要是使用MultiAgent的思路，让大模型生成单元测试（UT）代码，具体方法记录在文档[UT启动+多Agent实验
](https://doc.weixin.qq.com/doc/w3_APIA0QZ_ACcu8WdDeLxQBCx92Cw9f?scode=AJEAIQdfAAon0yNwodAPIA0QZ_ACc)
主要参考了[ChatTester](https://arxiv.org/abs/2305.04207)和[AgentcCoder](https://arxiv.org/html/2312.13010v2)
的思路，其主要步骤分为两个大步骤

## 第1步 初始UT代码生成
第1步Prompt主要做下面的工作
- 1、根据被测代码类型设计测试用例生成种类的指令；
- 2、因为后面需要执行代码，所以python这里让模型基于unittest格式来写UT代码；
- 3、为了方便后面的用例修改，这里让每个unittest函数尽可能只有一个测试用例。

## 第2步 迭代修改UT代码
第2步主要做下面的工作
- 1、执行第一步中的UT代码，python这里选用了subprocess 的 Popen来执行并拿到报错信息；
- 2、让大模型根据错误信息来修改UT代码，这里是利用了大模型的自省能力；
- 3、修再执行改后的UT代码，拿到错误信息，继续让大模型来修改，直到没有错误或者达到迭代次数限制。。

# 文件结构

```Text
.
|-- tidy_res                      # 统计多轮迭代的结果，里面he_res.json是一个优化一轮的样例
|-- eval_pipline_local.py         # 使用huggingface的Transformers的本地调用样例，包含全部流程，优先看懂
|-- he_data.json                  # human-eval的164道题，已经拼接好，能保证逻辑完全正确的被测代码
|-- refiner_agent.py              # 迭代优化的Agent
|-- refiner_prompt.md             # 迭代优化Agent的Prompt模板
|-- tester_agent.py               # 生成初始UT的Agent
|-- tester_prompt.md              # 生成初始UT的Agent的Prompt模板
|-- utils.py                      # 工具部分，通用部分处理， run_by_subprocess 是执行python代码UT的函数
```
