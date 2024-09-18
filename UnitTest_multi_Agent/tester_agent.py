
import time

from utils import get_llm_response, extract_python_result,get_llm_completions

class TesterAgent:
    def __init__(self, prompt_file = "tester_prompt.md"):
        # 读取prompt模板
        with open(prompt_file, "r", encoding='utf-8') as f:
            self.tester_prompt_template = f.read()
    

    def get_code_to_test(self,code_file):
        # 读取代码
        with open(code_file, "r", encoding='utf-8') as f:
            code_to_test = f.read()
        
        # 确定代码类型
        code_type = code_file.split(".")[-1]
        if code_type == "py":
            code_type = "python"
            test_framework = 'unittest'
        
        # 补充上代码类型
        code_to_test = "```" + code_type + "\n" + code_to_test + "\n```"

        return code_type, code_to_test, test_framework
        

    def generate_prompt(self, code_type, code_to_test,test_framework):
        # 拼成prompt
        tester_prompt = self.tester_prompt_template.format(
            code_type = code_type,
            code_to_test = code_to_test,
            test_framework = test_framework
        )
        return tester_prompt
    
    def generte_unit_result(self, code_type, code_to_test, test_framework):
        """
        写一个pipline
        """
        pass
        
    

if __name__ == "__main__":
    tester = TesterAgent("tester_prompt.md")
    code_file = 'sample_code.py'
    start_time = time.time()
    code_type, code_to_test, test_framework = tester.get_code_to_test(code_file)
    # print("code_to_test: ", code_to_test)
    prompt = tester.generate_prompt(code_type, code_to_test,test_framework)
    print(prompt)
    res_json = get_llm_completions(prompt)
    # print("res_json: ", res_json)
    res_content = res_json['choices'][0]['message']['content']
    # print("模型输出: ",res_content)
    test_code = extract_python_result(res_content)
    print(test_code)
    print("\n")
    stop_time = time.time()
    print("best of 2 总耗时: ", stop_time - start_time)
    print("\n")
    print("Run Test")
    res = exec(test_code)
    print(res)
    
    exit(0)
    
    tester = TesterAgent("simple_tester_prompt.md")
    code_file = 'samples.py'
    start_time = time.time()
    code_type, code_to_test = tester.get_code_to_test(code_file)
    # print("code_to_test: ", code_to_test)
    prompt = tester.generate_prompt(code_type, code_to_test)
    print(prompt)
    res_json = get_llm_response(prompt)
    # print("res_json: ", res_json)
    res_content = res_json['choices'][0]['message']['content']
    print("模型输出: ",res_content)
    test_code = tester.extract_python_result(res_content)
    print("test_code: \n",test_code)
    print("\n")
    stop_time = time.time()
    print("best of 2 总耗时: ", stop_time - start_time)
    
    exit(0)