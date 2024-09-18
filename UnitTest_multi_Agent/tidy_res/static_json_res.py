import json

"""
data[0].keys(): dict_keys(['task_id', 'code_to_test', 'round_res'])
data[0]['round_res'][0].keys() :dict_keys(['round', 'unit_test_code', 'run_info', 'total_cases', 'bug_num', 'pass_num', 'refine_prompt'])
"""
# 读取json文件
def read_json(file_name):
    with open(file_name, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

# 处理多轮结果
def tidy_a_round(data,round_num):
    # 这里要统计一轮的结果
    # 处理信息包含：测试用例数，bug数，pass数这些平均数，然后总体通过率，每一个样本的通过率这样
    # 备注：因为每个测试function内可能会有多个Assert，但是unit_test只会按函数统计
    # 这里添加了对每个函数测试用例数目的指导，即一个函数内写一个assert，但是模型并不会严格遵守就是了
    detail_res = []
    pass_rate_list = []
    total_cases = 0
    total_bug = 0
    total_pass = 0
    # 很多样本该轮次是没有结果的
    total_samples = len(data)
    round_samples = 0
    # 加一个pass全过的样本统计
    total_all_pass = 0
    
    """
    这里按整体论次会有一个问题
    round 0: {'total_cases': 657, 'total_case_rate': 4.080745341614906, 'total_bug': 110, 'total_pass': 547, 'total_pass_rate': 0.832572298325723, 'round_samples': 161, 'total_samples': 162, 'round_sample_rate': 0.9938271604938271}
    round 1 :{'total_cases': 295, 'total_case_rate': 4.538461538461538, 'total_bug': 85, 'total_pass': 210, 'total_pass_rate': 0.711864406779661, 'round_samples': 65, 'total_samples': 162, 'round_sample_rate': 0.4012345679012346}
    total_pass_rate 不增反降，应该是到第二轮的题都比较难，而且不容易改对，所以要单独统计这些题，还有就是要做个“真平均分”
    真平均分： 取最后的论次，之前对的也统计进来，实际意义为“截止该轮” 的通过率
    """
    # 这三个统计真平均分
    real_total_cases = 0
    real_total_pass = 0
    real_total_bug = 0
    real_round_samples = 0
    real_all_pass = 0
    
    # 这里统计有结果上一轮的
    last_total_cases = 0
    last_total_pass = 0
    last_total_bug = 0
    last_round_samples = 0
    last_all_pass = 0
    
    
    
    for each_sample in data:
        sample_rounds = len(each_sample['round_res'])
        if sample_rounds <= round_num :
            # 没有该轮次的结果，跳过，但是要统计real的结果，就是优化最后一轮结果
            detail_res.append({"cases" : -1})
            pass_rate_list.append(-1)
            if sample_rounds == 0 or round_num == 0:
                continue
            real_test_res = each_sample['round_res'][sample_rounds - 1]
            if(real_test_res['run_info'] == "Exception"):
                continue
            real_total_cases += real_test_res['total_cases']
            real_total_bug += real_test_res['bug_num']
            real_total_pass += real_test_res['pass_num']
            real_round_samples += 1
            if real_test_res['pass_num'] == real_test_res['total_cases'] and real_test_res['total_cases'] > 0:
                real_all_pass += 1

            continue
        # 检查一下UT运行额度结果是否正确
        if each_sample['round_res'][round_num]['run_info']  == "Exception":
            continue
        round_samples += 1
        test_res = each_sample['round_res'][round_num]
        temp_res = {"cases": test_res['total_cases'], "bug": test_res['bug_num'], "pass": test_res['pass_num']}
        if test_res['total_cases'] != 0:
            pass_rate = test_res['pass_num'] / test_res['total_cases']
        else:
            pass_rate = -1
        temp_res['pass_rate'] = pass_rate
        detail_res.append(temp_res)
        pass_rate_list.append(pass_rate)
        # 统计总数
        total_cases += test_res['total_cases']
        total_bug += test_res['bug_num']
        total_pass += test_res['pass_num']
        if test_res['pass_num'] == test_res['total_cases'] and test_res['total_cases'] > 0:
            total_all_pass += 1
        
        # 这些难题的上轮统计
        if round_num > 0:
            last_test_res = each_sample['round_res'][round_num - 1]
            if(last_test_res['run_info'] == "Exception"):
                continue
            last_total_cases += last_test_res['total_cases']
            last_total_bug += last_test_res['bug_num']
            last_total_pass += last_test_res['pass_num']
            last_round_samples += 1
            if last_test_res['pass_num'] == last_test_res['total_cases'] and last_test_res['total_cases'] > 0:
                last_all_pass += 1
    
    if round_samples != 0:
        round_sample_rate = float(round_samples) / total_samples
    else:
        round_sample_rate = -1
        print("No Result")
        return None , None , None
    
    # 本轮次的结果
    total_pass_rate = float(total_pass) / total_cases
    total_case_rate = float(total_cases) / round_samples
    total_all_pass_rate = float(total_all_pass) / round_samples

    # 上轮次的结果
    if round_num > 0:
        last_total_pass_rate = float(last_total_pass) / last_total_cases
        last_total_case_rate = float(last_total_cases) / last_round_samples
        last_all_pass_rate = float(last_all_pass) / last_round_samples
    else:
        last_total_pass_rate = -1
        last_total_case_rate = -1
        last_all_pass_rate = -1

    # 本轮次真实结果
    real_total_pass_rate = float(real_total_pass + total_pass) / (total_cases + real_total_cases)
    real_total_sample_rate = float(real_total_cases + total_cases) / (real_round_samples + round_samples)
    real_all_pass_rate = float(real_all_pass + total_all_pass) / (real_round_samples + round_samples)
    
    res_json = {"total_cases": total_cases,
                "total_case_rate": total_case_rate, 
                "total_bug": total_bug, 
                "total_pass": total_pass, 
                "total_pass_rate": total_pass_rate, 
                "round_samples": round_samples, 
                "total_samples": total_samples, 
                "round_sample_rate": round_sample_rate, 
                "total_all_pass": total_all_pass,
                "total_all_pass_rate": total_all_pass_rate,

                "last_total_pass": last_total_pass, 
                "last_total_cases": last_total_cases, 
                "last_total_pass_rate": last_total_pass_rate, 
                "last_total_case_rate": last_total_case_rate, 
                "last_round_samples": last_round_samples, 
                "last_all_pass": last_all_pass,
                "last_all_pass_rate": last_all_pass_rate,

                "real_total_pass": real_total_pass, 
                "real_total_cases": real_total_cases, 
                "real_round_samples": real_round_samples,
                "real_total_pass_rate": real_total_pass_rate,
                "real_total_sample_rate": real_total_sample_rate,
                "real_all_pass": real_all_pass,
                "real_all_pass_rate": real_all_pass_rate,
                }
    
    print("res_json")
    print(res_json)
    
    return res_json, detail_res, pass_rate_list

if __name__ == "__main__":
    #data = read_json("he_res.json")
    data = read_json("../he_res_tester_prompt_5_round.json")
    for i in range(0,6):
        print("round ",i)
        res_json, detail_res, pass_rate_list = tidy_a_round(data, i)
        print("\n")
