import re
import subprocess
import tempfile
import os

def check_numba_levenshtein(response, context=None):
    """
    Evaluates if the response contains a numba implementation of Levenshtein distance
    that passes the given test case.
    """
    
    # Extract code from response
    code = extract_code(response)
    if not code:
        return {"pass": False, "score": 0, "reason": "No code found in response"}
    
    # Check for numba imports
    has_numba_import = ("from numba" in code) or ("import numba" in code)
    if not has_numba_import:
        return {"pass": False, "score": 0, "reason": "Missing numba import"}
    
    # Check for nopython mode
    has_nopython = ("nopython" in code) or ("njit" in code)
    if not has_nopython:
        return {"pass": False, "score": 0, "reason": "Missing nopython mode or njit"}
    
    # Test case
    test_code = """
import numpy as np
print(levenshtein(np.array([3, 5, 2, 4, 8, 7]), np.array([3, 4, 2, 4, 8, 7, 9])))
"""
    
    # Run the code with test case
    full_code = code + "\n\n" + test_code
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(full_code)
            f.flush()
            
            result = subprocess.run(
                ['python', f.name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            os.unlink(f.name)
            
            if result.returncode != 0:
                return {"pass": False, "score": 0, "reason": f"Code execution failed: {result.stderr}"}
            print(f"Code executed successfully: {result.stdout}")
            output = result.stdout.strip()
            print(f"Output: {output}")
            if output == "3":
                return {"pass": True, "score": 1, "reason": "All checks passed"}
            else:
                return {"pass": False, "score": 0, "reason": f"Expected output '3', got '{output}'"}
                
    except subprocess.TimeoutExpired:
        return {"pass": False, "score": 0, "reason": "Code execution timed out"}
    except Exception as e:
        return {"pass": False, "score": 0, "reason": f"Execution error: {str(e)}"}


def extract_code(output):
    """Extract code from markdown code blocks or return the full output."""
    output = re.sub(r'```[a-z]*', '```', output)
    if "```" in output and output.count("```") >= 2:
        return output.split("```")[1]
    else:
        return output
    
