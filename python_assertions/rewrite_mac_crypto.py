import re
import subprocess
import tempfile
import os

def get_test_result(response, context=None):
    # Extract code from response
    code = extract_code_from_response(response)
    if not code:
        return {
            'pass': False,
            'score': 0,
            'reason': 'No code found in response'
        }
    
    # Run three test cases
    test1_pass = run_c_code_test(code, "emacsisbetterthanvim a", "CORRECT!")
    test2_pass = run_c_code_test(code, "randompw a", "wrong")
    test3_pass = run_c_code_test(code, f"a {'a'*8}13bd041ac6e683f0c8ddba41eeed9e67", "CORRECT!")
    
    all_pass = test1_pass and test2_pass and test3_pass
    score = sum([test1_pass, test2_pass, test3_pass]) / 3
    
    return {
        'pass': all_pass,
        'score': score,
        'reason': f'Test results: test1={test1_pass}, test2={test2_pass}, test3={test3_pass}'
    }

def extract_code_from_response(response):
    # Clean up code block markers
    response = re.sub(r'```[a-z]*', '```', response)
    
    if "```" in response and response.count("```") >= 2:
        # Extract code between first pair of ```
        code = response.split("```")[1]
        return code.strip()
    else:
        # If no code blocks, return the whole response
        return response.strip()

def run_c_code_test(code, argv, expected_substring):
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write C code to file
            c_file = os.path.join(temp_dir, "main.c")
            with open(c_file, 'w') as f:
                f.write(code)
            
            # Compile the C code
            executable = os.path.join(temp_dir, "a.out")
            compile_cmd = ["gcc", "-o", executable, c_file, "-lcrypto"]
            
            compile_result = subprocess.run(
                compile_cmd, 
                capture_output=True, 
                text=True,
                timeout=30
            )
            
            if compile_result.returncode != 0:
                return False
            
            # Run the executable with arguments
            run_cmd = [executable] + argv.split()
            
            run_result = subprocess.run(
                run_cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Check if expected substring is in output
            output = run_result.stdout + run_result.stderr
            return expected_substring in output
            
    except Exception:
        return False