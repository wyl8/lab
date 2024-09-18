import sys
from io import StringIO
import contextlib
from contextlib import redirect_stdout,redirect_stderr

import os
import shutil
from subprocess import Popen, PIPE, run

import requests
import json

def get_llm_completions(prompt):
    """
    curl --location 'http://42.192.32.62:8005/v1/completions' \
    --header 'Content-Type: application/json' \
    --data '{
        "model":"codewise-chat",
        "max_tokens":500,
        "temperature":0,
        "top_p":1,
        "n":1, 
        "stream":false,
        "prompt":"你好!\n ##Response:",
        "stop":["<|EOT|>"]
    }'
    """
    model_url = "http://42.192.32.62:8005/v1/completions"
    headers = {'Content-Type': 'application/json'}
    data = {
            "model":"codewise-chat",
            "max_tokens":3000,
            "temperature":0,
            "top_p":1,
            "n":1, 
            "stream":False,
            "stop":["<|EOT|>"],
            "prompt": prompt
    }
    res_json = None

    try:
        response = requests.post(model_url, headers=headers, data=json.dumps(data))
        res_json = response.json()
        status_code = response.status_code
        if status_code != 200:
            print("请求失败，状态码: ", status_code)
            res_json = {"error": str(e)}
            return None
    except Exception as e:
        res_json = {"error": str(e)}
        return None
    
    
    res_content = res_json['choices'][0]['text']
    print(res_content)
    return res_content

def get_llm_response(prompt):
    """
    请求deepseek-coder-7b-instruct-v1.5 + dummy 模型
    curl --location '42.192.32.62:8005/v1/chat/completions' \
    --header 'Content-Type: application/json' \
    --data '{
        "model": "codewise-chat",
        "stream": false,
        "temperature": 0,
        "messages": [
        {
            "role": "user",
            "content": "你好！"
        }
        ]
    }'

    有一定几率会超时
    """
    model_url = "http://42.192.32.62:8005/v1/chat/completions"
    headers = {'Content-Type': 'application/json'}
    data = {
            "model": "codewise-chat",
            "max tokens": 4000,
            "stream": False,
            "temperature": 0,
            "use_beam_search": True,
            "best_of": 2,
            "n": 1, 
            "messages": 
            [
                
                {
                    "role": "user",
                    "content": prompt
                }
            ]
    }
    """
      File "/data/anaconda3/envs/huggingface_transformers/lib/python3.10/http/client.py", line 287, in _read_status
        raise RemoteDisconnected("Remote end closed connection without"
    http.client.RemoteDisconnected: Remote end closed connection without response
    """
    res_json = None

    try:
        response = requests.post(model_url, headers=headers, data=json.dumps(data))
        res_json = response.json()
        status_code = response.status_code
        if status_code != 200:
            print("请求失败，状态码: ", status_code)
            res_json = {"error": str(e)}
            return None
    except Exception as e:
        res_json = {"error": str(e)}
        return None
    
    res_content = res_json['choices'][0]['message']['content']

    return res_content

def get_llm_response_local(prompt,model,tokenizer):
    """
    这里是本地调用LLM使用的，测试子健的模型
    这里有一个问题，就是model不要每次读取，所以这里需要保留一个model的实例
    """
    result = None
    
    messages=[
    { 'role': 'user', 'content': prompt}
    ]
    inputs = tokenizer.apply_chat_template(messages, add_generation_prompt=True, return_tensors="pt").to(model.device)
    # print('### Input: ', tokenizer.decode(inputs.input_ids[0], skip_special_tokens=False))

    outputs = model.generate(inputs, max_new_tokens=4096, do_sample=False, top_k=50, top_p=0.95, num_return_sequences=1, eos_token_id=tokenizer.eos_token_id) # eos_token_id=100015 | 32014 | 32021 | 49155)
    result = tokenizer.decode(outputs[0][len(inputs[0]):], skip_special_tokens=True)
    print('### Output: ', result)

    return result
    

def extract_python_result(res_code):
    """
    Here is a unit test for the given python code:

    ```python
    import unittest
    ......
    ......
    ......
    if __name__ == '__main__':
        unittest.main()
    ```
    """
    # 为了处理以上结果，统一寻找代码部分格式，并进行字典转换，如果失败，则返回原文吧
    find_flag = False
    start_index = 0
    end_index = len(res_code)
    code_str = ''
    while not find_flag :
        try:
            start_index = res_code.index("```python", start_index)
            end_index = res_code.index("```", start_index + 1)
            code_str = res_code[start_index + len("```python") : end_index]
            code_str = code_str.strip()
        except:
            # 到这里就是找不到结果了
            break
        
        if "unittest" in code_str:
            find_flag = True
            break
        else:
            start_index = start_index + 1
            continue

    # 没找到结果
    if not find_flag:
        code_str = "error: 未找到结果"
        print("未找到结果")
        print("res_code: ", res_code)
        print("未找到结果")

    return code_str
    
@contextlib.contextmanager
def stdout_io(stdout=None):
    """
    重定向sys.stdout输出
    """
    old = sys.stdout
    if stdout is None:
        stdout = StringIO()
    sys.stdout = stdout
    yield stdout
    sys.stdout = old

def make_run_code(code_to_test,unit_test_code,entry_point):
    # 修改单测代码
    # 1、如果不包含被测试函数，就插入被测函数
    # 2、要unittest执行后不退出
    # 3、会有这类引入 from entry_point import entry_point，from your_module_name import is_palindrome, make_palindrome 需要删除

    run_code = unit_test_code

    function_import = "import " + entry_point
    if function_import in run_code:
        #寻找 from 和换行，去除这一行
        import_index = run_code.index(function_import)
        end_index = run_code.index("\n", import_index)
        strat_index = import_index
        for i in range(import_index, 4, -1):
            if run_code[i-4:i] == "from":
                strat_index = i-4
                break
            
        run_code = run_code[:strat_index] + run_code[end_index:]

    function_sign = "def " + entry_point

    if function_sign not in run_code:
        try:
            strat_index = run_code.index("class")
        except:
            strat_index = 0
        run_code = run_code[:strat_index] + code_to_test +"\n\n" + run_code[strat_index:]
    
    if "unittest.main()" in run_code:
        run_code = run_code.replace("unittest.main()", "unittest.main(exit=False)")
    
    return run_code


def run_by_subprocess(entry_point,unit_test_code):
    """
    这里先考虑一下怎么使用命令行执行unittest
    1、只用python，需要代码内有入口
    if __name__ == '__main__':
        unittest.main(exit=False)
    2、使用module调用 python -m unittest，有无main入口都可以，这里先选用这种，后面有坑再说
    """
    run_info = "Exception"
    # 建立临时文件
    tmp_dir_name = "test_" + entry_point
    tmp_file_name = "test_" + entry_point + ".py"
    if not os.path.exists(tmp_dir_name):
        os.makedirs(tmp_dir_name)
    tmp_file_name = os.path.join(tmp_dir_name, tmp_file_name)
    with open(tmp_file_name, 'w',encoding='utf-8') as f:
        f.write(unit_test_code)
    
    #执行测试
    cmd = "python -m unittest " + tmp_file_name
    try:
        proc = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        out, error = proc.communicate(timeout=10)
        run_info = error.decode('utf-8')
    except Exception as e:
        print("Exception: ",e)
        proc.terminate()
        run_info = "Exception"
    
    #清理临时文件
    shutil.rmtree(tmp_dir_name)

    return run_info
