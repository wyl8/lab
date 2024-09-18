import time
import json
import torch 
from deepseek_vl.models import VLChatProcessor, MultiModalityCausalLM
from deepseek_vl.utils.io import load_pil_images
import pdb

# specify the path to the model


from transformers import AutoTokenizer, AutoModelForCausalLM

from utils import get_llm_response_local, extract_python_result,make_run_code,run_by_subprocess
from tester_agent import TesterAgent
from refiner_agent import RefinerAgent




def load_json_data(file_name):
    with open(file_name, 'r') as f:
        data = json.load(f)
    print("load_json_data: ",len(data))
    return data


if __name__ == "__main__":
    """
    这个是本地运行的，需要一个model和一个tokenizer
    """
    model_path = "deepseek-ai/deepseek-coder-1.3b-instruct"
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(model_path, 
                                                 torch_dtype=torch.float16, 
                                                 trust_remote_code=True).cuda()
    tester_agent = TesterAgent("tester_prompt.md")
    refinder_agent = RefinerAgent("refiner_prompt.md")
    code_type = "python"
    test_framework = "unittest"

    # 保存结果记录
    res_list = []
    
    # {task_id,code,entry_point}
    new = load_json_data("new.json")
    for each_example in new:
        task_id = each_example['task_id']
        code_to_test = each_example['code_to_test']
        entry_point = each_example['entry_point']
        unit_test_code = ""
        run_code = ""
        
        print("Now processing task_id: ", task_id)
        start_time = time.time()
        # 记录运行结果
        res_dict = {}
        res_dict['task_id'] = task_id
        res_dict['code_to_test'] = code_to_test
        res_dict['round_res'] = []
        
        data = each_example['round_res']
        
        
        unit_test_code = data[0]['unit_test_code']
        #pdb.set_trace()
        print("unit_test_code")
        print(unit_test_code)
        refine_prompt = data[0]['round_prompt']

        for i in range(0,6):
            print("\n")
            print("Start Refine round: ", i+1)
            print("Run Test")
            # run_info = exec_unit_test(unit_test_code)
            run_code = make_run_code(code_to_test,unit_test_code,entry_point)
            # run_code = unit_test_code.replace("if __name__ == '__main__':\n    unittest.main()", "unittest.main(exit=False)")
            print(run_code)
            # 运行单测代码
            run_info = run_by_subprocess(entry_point,run_code)
            print("run_info:")
            print(run_info)
            print("run_info:")
            
            round_res = {}
            round_res['round'] = i
            round_res['unit_test_code'] = unit_test_code
            round_res['run_info'] = run_info
            round_res['round_prompt'] = refine_prompt
            
            
            if run_info == "Exception":
                print("run_code:")
                print(run_code)
                print("单测代码自身错误，放弃优化测试用例")
                res_dict['round_res'].append(round_res)
                break
            refinder = RefinerAgent("refiner_prompt.md")
            bug_num, pass_num, unit_test_code = refinder.get_unit_test_code(code_type,test_framework,unit_test_code,run_info)
            print("bug_num: ",bug_num, " pass_num: ", pass_num)

            round_res['total_cases'] = bug_num + pass_num
            round_res['bug_num'] = bug_num
            round_res['pass_num'] = pass_num
            if bug_num == 0:
                print("单测用例全部通过，无需优化")
                res_dict['round_res'].append(round_res)
                break
            refine_prompt = refinder.generate_prompt(code_type, code_to_test,test_framework,
                                                    unit_test_code,bug_num,run_info)
            # print("refine_prompt")
            # print(refine_prompt)

            res_json = get_llm_response_local(refine_prompt,model,tokenizer)
            if not res_json :
                print("模型无响应")
                break
            res_content = res_json
            unit_test_code = extract_python_result(res_content)
            # print("refine_ut")
            # print(res_content)
            res_dict['round_res'].append(round_res)

        res_list.append(res_dict)
        # 怕出错，每题保存一下吧
        with open("he_res_tester_prompt_5_round.json","w",encoding="utf-8") as f:
            json.dump(res_list,f,ensure_ascii=False,indent=4)

        stop_time = time.time()
        print("总耗时: ", stop_time - start_time)
        print("\n")
    
    
    exit(0)
    