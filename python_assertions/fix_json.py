import re
import subprocess
import tempfile
import os

def check_fix_json_function(response, context=None):
    """
    Promptfoo assertion to test if the model can write a fix_json function.
    """
    try:
        # Extract code from response
        code = extract_code_from_response(response)
        if not code:
            return {"pass": False, "score": 0, "reason": "No code found in response"}
        
        # Test cases
        test_case = '''
# Test the fix_json function
result1 = fix_json(\'\'\'{"a": 5, "b": [3, 4]}\'\'\')
print("Test 1:", result1)

result2 = fix_json(\'\'\'{'a': 5.0, 'b': (True, 4)}\'\'\')
print("Test 2:", result2)

result3 = fix_json(\'\'\'{'True': False, 'b()': (3, 4), "c'": []}\'\'\')
print("Test 3:", result3)
'''
        
        # Run the code with test cases
        full_code = code + "\n\n" + test_case
        output = run_python_code(full_code)
        
        if output is None:
            return {"pass": False, "score": 0, "reason": "Code execution failed"}
        
        # Expected answer substring
        expected_answer = '''{"a": 5, "b": [3, 4]}
{"a": 5.0, "b": [True, 4]}
{"True": False, "b()": [3, 4], "c'": []}'''
        
        # Check if expected output is in the result
        if expected_answer in output:
            return {"pass": True, "score": 1, "reason": "All test cases passed"}
        else:
            return {"pass": False, "score": 0, "reason": f"Expected output not found. Got: {output}"}
            
    except Exception as e:
        return {"pass": False, "score": 0, "reason": f"Error during evaluation: {str(e)}"}

def extract_code_from_response(response):
    """Extract code from response, handling code blocks."""
    # Remove language specifiers from code blocks
    response = re.sub(r'```[a-z]*', '```', response)
    
    if "```" in response:
        # Extract code from code blocks
        if response.count("```") >= 2:
            return response.split("```")[1]
    
    # If no code blocks, return the whole response
    return response

def run_python_code(code):
    """Run Python code using subprocess and return output."""
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        # Run the code
        result = subprocess.run(
            ['python', temp_file],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Clean up
        os.unlink(temp_file)
        
        if result.returncode == 0:
            return result.stdout
        else:
            return None
            
    except Exception:
        return None