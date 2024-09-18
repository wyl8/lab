**Role**: : As a professional programmer, your task is to fix unit test code, which including comprehensive test cases. The original code writtern by {code_type} is shown in Code to Test part. The unit test code is based on {test_framework}, and is shown in Unit Test Code. There are {bug_num} errors in Unit Test Code and the bug info is shown in Bug Info. The Bug Info is produced by code exection. It includes the function name, buggy line number, and the error type. Please repair the bugs in Unit Test Code by the information from Bug Info.

**Code to Test**: 
{code_to_test}

**Unit Test Code**: 
{unit_test_code}

**Bug Info**: 
{bug_info}

**Instructions**:
- Please repair the bugs in Unit Test Code by the information from Bug Info.
- Try to fix bug by only edit the error line. If editing other lines are needed, please edit as few lines as possible.
- Do not make any changes to the functions without errors.
- Ensure the assert sentences are right.
- Please do not fix bugs that are not mentioned in the bug info

**Output**:
