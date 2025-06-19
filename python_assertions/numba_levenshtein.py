import subprocess
import tempfile
import os
import re
import numpy as np

def get_assertion(response, context=None):
    """
    Evaluates if the response contains a valid numba implementation of Levenshtein distance.
    """
    
    # Step 1: Extract code from response
    def extract_code(output, keep_main=False):
        output = re.sub('```[a-z]*', '```', output)
        if "```" in output and output.count("```") >= 2:
            # Extract code between first pair of ```
            parts = output.split("```")
            if len(parts) >= 3:
                return parts[1].strip()
        # If no code blocks found, return the whole output
        return output.strip()
    
    extracted_code = extract_code(response)
    
    # Step 2: Check for numba imports
    has_numba_import = ("from numba" in extracted_code or "import numba" in extracted_code)
    
    # Step 3: Check for nopython mode
    has_nopython = ("nopython" in extracted_code or "njit" in extracted_code)
    
    if not (has_numba_import and has_nopython):
        return {
            "pass": False,
            "score": 0,
            "reason": f"Missing requirements - numba import: {has_numba_import}, nopython mode: {has_nopython}"
        }
    
    # Step 4: Prepare test case
    test_case = """
import numpy as np
result = levenshtein(np.array([3, 5, 2, 4, 8, 7]), np.array([3, 4, 2, 4, 8, 7, 9]))
print(result)
"""
    
    # Step 5: Run the code with test case
    full_code = extracted_code + "\n\n" + test_case
    
    try:
        # Create a temporary file with UTF-8 encoding
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(full_code)
            temp_file = f.name
        
        # Run the code with UTF-8 encoding
        result = subprocess.run(
            ["python", temp_file],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',  # This will ignore any characters that can't be decoded
            timeout=30
        )
        
        # Clean up
        os.unlink(temp_file)
        
        if result.returncode != 0:
            return {
                "pass": False,
                "score": 0,
                "reason": f"Code execution failed: {result.stderr}"
            }
        
        # Step 6: Check if output matches expected answer
        output = result.stdout.strip()
        expected_answer = "3"
        
        if expected_answer in output:
            return {
                "pass": True,
                "score": 1,
                "reason": "All tests passed: numba implementation with correct output"
            }
        else:
            return {
                "pass": False,
                "score": 0.5,
                "reason": f"Code runs but incorrect output. Expected: {expected_answer}, Got: {output}"
            }
            
    except subprocess.TimeoutExpired:
        if 'temp_file' in locals():
            os.unlink(temp_file)
        return {
            "pass": False,
            "score": 0,
            "reason": "Code execution timed out"
        }
    except Exception as e:
        if 'temp_file' in locals():
            os.unlink(temp_file)
        return {
            "pass": False,
            "score": 0,
            "reason": f"Error during execution: {str(e)}"
        }