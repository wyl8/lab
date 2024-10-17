import json
import pickle

from embedding_agent import EmbeddingAgent


"""
统计日期	工单ID	一级标签	二级标签	三级标签	四级标签	内部反馈人组织架构	原始诉求	解决方案	url	透传类别
卡片这里 
一级标签：工具类型
二级标签：一个是如果你可以查出来项目ID，那就是InquireRole。查不出来就InquireRoleExcludeID
"""
def loda_data(file_name):
    with open(file_name,'r',encoding='utf-8') as f:
        lines = f.readlines()
    print(len(lines))
    all_titles = lines[0].strip().split('\t')
    print(all_titles)
    print(len(all_titles))
    # 去掉第一行
    data = [line.strip() for line in lines[1:]]
    # 要不就就干脆整个字典的格式算了，后面拼的时候直接去读，读不到再报错，就这么愉快额度决定了吧，type也不用回了，这里就用type来做特别不同位置的处理，还真没啥重复的部分，直接分开搞
    # 还有很多重复的，这里去重一下吧
    data_list = []
    duplicate_query = []
    for eachline in data:
        tmp_dict = {}
        eachlist = eachline.strip().split('\t')
        """
        if len(eachlist) != 11:
            print(" 格式错误")
            print(eachlist)
            continue
        """
        tmp_dict['公司名称'] = eachlist[0]
        tmp_dict['公司规模'] = eachlist[1]
        tmp_dict['岗位'] = eachlist[2]
        tmp_dict['公司位置'] = eachlist[3]
        tmp_dict['年薪'] = eachlist[4]
        tmp_dict['经验要求'] = eachlist[5]
        tmp_dict['basic'] = eachlist[6]
        tmp_dict['ID'] = eachlist[7]
        # 过短数据处理
        """
        if len(tmp_dict['ori_query']) < 4:
            print("过短数据  ID:", tmp_dict['ID'], "  原始诉求:", tmp_dict['ori_query'])
            continue
        
        if tmp_dict['basic'] in duplicate_query:
            print("重复数据  ID:", tmp_dict['ID'], "  原始诉求:", tmp_dict['basic'])
            continue
        else:
            duplicate_query.append(tmp_dict['basic'])
        """   
        data_list.append(tmp_dict)
        
    print("去重整理后得到：", len(data_list))

    return data_list

def make_search_data(data_list, embedding_key = 'basic'):
    embedding = EmbeddingAgent()
    # 这里统一改成字典的样式了，所以字段统一用 'ori_query' 这个字段了
    search_data = []
    for eachdict in data_list:
        if embedding_key not in eachdict.keys():
            print(embedding_key + " 字段不存在")
            continue
        ori_query = eachdict[embedding_key]
        ori_query_embedding = embedding.get_embedding(ori_query)
        search_data.append(ori_query_embedding)
    print("len(search_data[0]): ", len(search_data[0]))
    return search_data


if __name__ == '__main__':
    data_list  = loda_data('2024_7_7_岗位_new.txt')
    print(len(data_list))
    with open('2024_7_7_岗位_new', 'w',encoding='utf-8') as f:
        json.dump(data_list, f, indent=4, ensure_ascii=False)
    print("Finish Write Json")
    embedding_list = make_search_data(data_list)
    print(len(embedding_list))
    with open('2024_7_7_岗位_new.pickle', 'wb') as f:
        pickle.dump(embedding_list, f)