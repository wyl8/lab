
import time
from contextlib import redirect_stderr
from io import StringIO


from utils import get_llm_response,extract_python_result
from tester_agent import TesterAgent

class RefinerAgent:
    def __init__(self, prompt_file = "refiner_prompt.md"):
        # 读取prompt模板
        with open(prompt_file, "r", encoding='utf-8') as f:
            self.refiner_prompt_template = f.read()
    

    def get_unit_test_code(self,code_type,test_framework,unit_test_code,run_info):
        # 这里先提取出bug的数量，通过的数量
        bug_num = 0
        pass_num = 0
        # 确定测试代码类型来处理代码类型吗，这里先写python的
        if code_type == "py" or "python":
            if test_framework == 'unittest':
                """
                ....FF.
                ======================================================================
                FAIL: test_edge_case_3 (__main__.TestHasCloseElements)
                Test with a threshold of zero.
                ----------------------------------------------------------------------
                Traceback (most recent call last):
                File "<string>", line 44, in test_edge_case_3
                AssertionError: False is not true

                ======================================================================
                FAIL: test_large_scale_case_1 (__main__.TestHasCloseElements)
                Test with a large list of numbers and a threshold.
                ----------------------------------------------------------------------
                Traceback (most recent call last):
                File "<string>", line 50, in test_large_scale_case_1
                AssertionError: True is not false

                ----------------------------------------------------------------------
                Ran 7 tests in 0.000s

                FAILED (failures=2)
                """
                # 如果是python的unittest，从第一行的.和F数目就能得到bug的数量和通过的数量
                run_info = run_info.strip()
                static_line = run_info.split("\n")[0]
                # ..F.......E.F...FFF.F......F.F.EF..
                bug_num = static_line.count("F") + static_line.count("E")
                pass_num = static_line.count(".")

        # 补充上代码类型
        unit_test_code = "```" + code_type + "\n" + unit_test_code + "\n```"

        return bug_num, pass_num, unit_test_code
        

    def generate_prompt(self, code_type, code_to_test,test_framework,
                        unit_test_code,bug_num,bug_info):
        # 拼成prompt
        refiner_prompt = self.refiner_prompt_template.format(
            code_type = code_type,
            code_to_test = code_to_test,
            test_framework = test_framework,
            unit_test_code = unit_test_code,
            bug_num = bug_num,
            bug_info = bug_info,
        )
        return refiner_prompt


if __name__ == "__main__":
    tester = TesterAgent("tester_prompt.md")
    code_file = 'sample_code.py'
    start_time = time.time()
    code_type, code_to_test, test_framework = tester.get_code_to_test(code_file)
    prompt = tester.generate_prompt(code_type, code_to_test,test_framework)
    res_json = get_llm_response(prompt)
    res_content = res_json['choices'][0]['message']['content']
    test_code = extract_python_result(res_content)
    print("test_code")
    print(test_code)

    for i in range(0,2):
        print("\n")
        print("Start Refine round: ", i+1)
        print("Run Test")
        # run_info = exec_unit_test(test_code)
        run_code = test_code.replace("unittest.main()", "unittest.main(exit=False)")
        f = StringIO()
        with redirect_stderr(f):
            exec(run_code)
        run_info = f.getvalue()
        print("run_info:")
        print(run_info)
        
        if run_info == "Exception":
            print("单测代码自身错误，放弃优化测试用例")
            exit(0)
        refinder = RefinerAgent("refiner_prompt.md")
        bug_num, pass_num, unit_test_code = refinder.get_unit_test_code(code_type,test_framework,test_code,run_info)
        print("bug_num: ",bug_num, " pass_num: ", pass_num)
        if bug_num == 0:
            print("单测用例全部通过，无需优化")
            exit(0)
        refine_prompt = refinder.generate_prompt(code_type, code_to_test,test_framework,
                                                unit_test_code,bug_num,run_info)
        print("refine_prompt")
        print(refine_prompt)
        res_json = get_llm_response(refine_prompt)
        res_content = res_json['choices'][0]['message']['content']
        test_code = extract_python_result(res_content)
        print("refine_ut")
        print(res_content)

    stop_time = time.time()
    print("best of 2 总耗时: ", stop_time - start_time)
    print("\n")
    
    exit(0)
