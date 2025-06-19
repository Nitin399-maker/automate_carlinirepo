import re
import subprocess
import tempfile
import os
def check_jax_one_hot(response, context=None):
    """
    Evaluates if the response contains a correct JAX one-hot function implementation.
    """
    
    # Step 1: Extract code from response
    def extract_code(output):
        # Remove language specifiers from code blocks
        output = re.sub(r'```[a-z]*', '```', output)
        if "```" in output and output.count("```") >= 2:
            # Extract code between first pair of backticks
            code = output.split("```")[1]
        else:
            # If no code blocks, assume entire response is code
            code = output
        return code.strip()
    
    extracted_code = extract_code(response)
    
    # Step 2: Prepare test case with mock JAX
    test_case = """
# Mock JAX numpy for testing
class MockJnp:
    def __init__(self):
        pass
        
    def array(self, arr):
        # Simple implementation using Python lists for testing
        return arr

jnp = MockJnp()

# Test the one_hot function
try:
    result = one_hot(jnp.array([1,2,0]), 5)
    
    # Convert result to a string representation for validation
    def format_result(res):
        if hasattr(res, 'shape') and hasattr(res, 'tolist'):
            # If it's a JAX or numpy array
            return str(res)
        else:
            # If it's our mock result (likely a list of lists)
            output = "["
            for row in res:
                output += "["
                output += " ".join([str(float(x)) + "." for x in row])
                output += "] "
            output += "]"
            return output
    
    print(format_result(result))
except Exception as e:
    print(f"Error testing one_hot function: {str(e)}")
"""
    
    # Step 3: Combine extracted code with test case
    full_code = extracted_code + "\n\n" + test_case
    
    # Step 4: Run Python code
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(full_code)
            temp_file = f.name
        
        result = subprocess.run(
            ['python', temp_file], 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        
        os.unlink(temp_file)
        
        if result.returncode != 0:
            return {
                'pass': False,
                'score': 0,
                'reason': f'Code execution failed: {result.stderr}'
            }
        
        output = result.stdout.strip()
        
    except subprocess.TimeoutExpired:
        return {
            'pass': False,
            'score': 0,
            'reason': 'Code execution timed out'
        }
    except Exception as e:
        return {
            'pass': False,
            'score': 0,
            'reason': f'Error running code: {str(e)}'
        }
    
    # Step 5: Check if output contains patterns that indicate a correct one-hot implementation
    # Check for error messages
    if "Error testing one_hot function" in output:
        return {
            'pass': False,
            'score': 0,
            'reason': f'Error in one_hot function: {output}'
        }
    
    # Look for patterns that would indicate a correct one-hot implementation
    # The result should have:
    # - For index 1: second position (index 1) is 1.0, rest are 0.0
    # - For index 2: third position (index 2) is 1.0, rest are 0.0
    # - For index 0: first position (index 0) is 1.0, rest are 0.0
    
    patterns_to_check = [
        # Check for row 1 (index 1 is hot)
        r'\[\s*0\..*1\..*0\..*0\..*0\..*\]',
        # Check for row 2 (index 2 is hot)
        r'\[\s*0\..*0\..*1\..*0\..*0\..*\]',
        # Check for row 0 (index 0 is hot)
        r'\[\s*1\..*0\..*0\..*0\..*0\..*\]'
    ]
    
    all_patterns_found = True
    for pattern in patterns_to_check:
        if not re.search(pattern, output):
            all_patterns_found = False
            break
    
    if all_patterns_found:
        return {
            'pass': True,
            'score': 1,
            'reason': 'One-hot function appears to work correctly'
        }
    else:
        return {
            'pass': False,
            'score': 0,
            'reason': f'Output doesn\'t match expected one-hot encoding pattern: {output}'
        }