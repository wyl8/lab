# -*- coding: utf-8 -*-
"""
@author: scarletliu
"""


from urllib.parse import unquote
import logging
from bottle import route, response, run, default_app, get, post, request

import json
import urllib.parse
from main_pipline import MainPipline

# 记录日志部分
logging.basicConfig(level=logging.DEBUG,
                format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                datefmt='%a, %d %b %Y %H:%M:%S',
                filename='./tagger_service.log',
                filemode='a')


global PIPLINE_OBJ
PIPLINE_OBJ = None
# 检查标注模型是否为空，如果为空则返回False，否则返回True

def CheckState():
    # 检查过滤器是否为空，如果为空则返回False，否则返回True
    global PIPLINE_OBJ
    if PIPLINE_OBJ is None \
        or PIPLINE_OBJ.checkstatus() is False: 
        return False
    return True

def InitAll():
    # 初始化过滤器并加载政治敏感词字典
    # 字典 too_sentitive_dict_keywords 过于宽泛，这里先用政治事件和人名的
    global PIPLINE_OBJ
    logging.debug('Init PIPLINE_OBJ !!')
    PIPLINE_OBJ = MainPipline()


InitAll()

# 主服务函数
@route('/query_tagger', method='POST')
def dev_step():
    global PIPLINE_OBJ
    uid = 'just_try_it'
    try:
        # 先检查过滤器是否为空，如果为空则初始化
        if CheckState() is False:
            InitAll()
        # 读取输入
        input_data = request.body.read()
        input_data = str(input_data, 'utf-8')
        # 支持json和HTTP两种格式
        try:
            dic = json.loads(input_data)
        except Exception as e :
            dic = dict(urllib.parse.parse_qsl(input_data))
        logging.debug('input= ' + input_data)
        if 'uid' in dic.keys():
            uid = dic['uid']
        # 提取输入    
        if 'user_query' in dic.keys():
            user_query = dic['user_query']
        else:
            logging.error('no user_query in input')
            return None
        
        # 设计一个返回字典格式
        resDict = {}
        query_attention = None
        # 逻辑修改了，卡片这里
        # 一级标签：工具类型
        # 二级标签：一个是如果你可以查出来项目ID，那就是InquireRole。查不出来就InquireRoleExcludeID
        attention_res = PIPLINE_OBJ.process_tags(query = user_query, top_k = 10)
        if 'error' in attention_res.keys():
            # 请求失败，进入兜底流程
            logging.error("意图获取失败")
            query_attention = '非工具类型'
        else: 
            query_attention = attention_res['一级标签']
        # 处理卡片
        if query_attention == '工具类型':
            card_info = PIPLINE_OBJ.process_card1(query = user_query)
            resDict['一级标签'] = attention_res['一级标签']
            # {'项目编号': '未找到', '项目角色': 'pmo'}
            if "项目编号" in card_info.keys() and card_info["项目编号"] == "未找到":
                resDict["二级标签"] = "InquireRoleExcludeID"
            else:
                resDict["二级标签"] = "InquireRole"
            # 目前三级和四级标签没有额外逻辑
            resDict['三级标签'] = attention_res['三级标签']
            resDict['四级标签'] = attention_res['四级标签']
            # 放后面纯粹为了输出好看
            resDict['card_info'] = card_info

        # 对问题进行1-4级标签分类
        else:
            resDict['一级标签'] = attention_res['一级标签']
            resDict['二级标签'] = attention_res['二级标签']
            # 目前三级和四级标签没有额外逻辑
            resDict['三级标签'] = attention_res['三级标签']
            resDict['四级标签'] = attention_res['四级标签']
        
        # 拼装返回结果和日志信息
        retDict = resDict
        debugDict = resDict
        logging.debug('return is:{}'.format(debugDict))
        retJson = json.dumps(retDict, ensure_ascii=False)
        return retJson
    # 异常处理
    except Exception as e:
        #返回错误
        logging.error('error is:{}'.format(e))
        retDict = {'retCode': -1, 'response': str(e), 'uid': uid}
        logging.debug('return is:{}'.format(retDict))
        retJson = json.dumps(retDict, ensure_ascii=False)
        return retJson
application = default_app()

