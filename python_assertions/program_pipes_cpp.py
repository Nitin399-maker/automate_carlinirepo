import re
import subprocess
import tempfile
import os

def assert_cpp_dataflow_dsl(response, context=None):
    """
    Evaluates if the LLM response contains C++ code that implements a dataflow DSL
    and produces the expected output when run with the test case.
    """
    
    # Extract code from response
    def extract_code(text):
        # Remove language specifiers from code blocks
        text = re.sub(r'```[a-z]*', '```', text)
        
        if "```" in text and text.count("```") >= 2:
            # Extract code from markdown code block
            code = text.split("```")[1]
        else:
            # Use the entire response as code
            code = text
            
        return code.strip()
    
    # Extract the code
    try:
        extracted_code = extract_code(response)
    except Exception as e:
        return False, f"Failed to extract code: {str(e)}"
    
    # Test case to append
    test_case = """int main() {
Const(2) >> Square() >> Inc() >> Square() >> Square() >> Print();
return 0;
}"""
    
    # Prepare the complete C++ code
    complete_code = extracted_code
    
    # Remove existing main function if present to avoid conflicts
    if 'int main' in complete_code and 'int main' in test_case:
        complete_code = complete_code.replace('int main', 'int __delete_this__main')
    
    complete_code = complete_code + "\n\n" + test_case
    
    # Create temporary files and compile/run
    with tempfile.TemporaryDirectory() as temp_dir:
        cpp_file = os.path.join(temp_dir, "main.cpp")
        exe_file = os.path.join(temp_dir, "a.out")
        
        try:
            # Write C++ code to file
            with open(cpp_file, 'w') as f:
                f.write(complete_code)
            
            # Compile the C++ code
            compile_result = subprocess.run(
                ['g++', '-o', exe_file, cpp_file, '-lm'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if compile_result.returncode != 0:
                return False, f"Compilation failed: {compile_result.stderr}"
            
            # Run the executable
            run_result = subprocess.run(
                [exe_file],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if run_result.returncode != 0:
                return False, f"Runtime error: {run_result.stderr}"
            
            # Check if output contains expected result
            output = run_result.stdout
            expected = "625"
            
            if expected in output:
                return {
                    "pass": True,
                    "score": 1,
                    "reason": f"Excepted:'{expected} , Output: {output.strip()}'"
                }
            else:
                return {
                    "pass": False,
                    "score": 0,
                    "reason": f"Excepted:'{expected} , Output: {output.strip()}'"
                }
                
        except subprocess.TimeoutExpired:
            return False, "Execution timed out"
        except Exception as e:
            return False, f"Execution failed: {str(e)}"