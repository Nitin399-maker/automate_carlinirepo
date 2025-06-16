import re
import subprocess
import tempfile
import os

def get_assertion(response, context=None):
    """
    Evaluates if the student's response correctly vectorizes the given loop.
    Returns True if both the code works correctly AND the student attempted vectorization.
    """
    
    # Extract code from the response
    def extract_code(output):
        output = re.sub('```[a-z]*', '```', output)
        if "```" in output and output.count("```") >= 2:
            return output.split("```")[1].strip()
        else:
            return output.strip()
    
    code = extract_code(response)
    
    # Test case and expected answer
    test_code = """
import numpy as np

# Insert the student's code here
{}

# Test the function
result = list(update(np.array([2, 5, 9, 1, 2, 0, 3, 8]), 4, np.array([1, 2, 1, 4, 3, 2, 1, 2])))
print(result)
""".format(code)
    
    expected_output = "[2, 3, 4, 1, 2, 0, 3, 3]"
    
    # Run the test case
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code)
            temp_file = f.name
        
        result = subprocess.run(['python', temp_file], capture_output=True, text=True, timeout=10)
        os.unlink(temp_file)
        
        if result.returncode != 0:
            return False
            
        output = result.stdout.strip()
        code_works = expected_output in output
        
    except Exception:
        return False
    
    # Check if student attempted vectorization
    evaluation_prompt = """Below is a student's answer to a question about how to vectorize this loop:

def update(high, highest_number, delta):
    for i in range(len(high)):
        if i != highest_number:
            high[i] = min(high[i], high[highest_number] + delta[highest_number] - delta[i])
    return high

Here is their code:

{}

Did the student try to vectorize the loop? Don't tell me if they are correct or not. (I have tests for that separately which will catch any bugs.) Just tell me if they tried to vectorize the loop. End your answer with either the string "The student passes" if they tried to do a vectorized loop, or "The student fails" if they just wrote a for loop again.""".format(code)
    
    # Simple heuristic check for vectorization attempt (avoiding LLM call)
    # Look for signs of vectorization: numpy operations, absence of explicit for loops
    vectorization_indicators = [
        'np.' in code,
        'numpy' in code,
        'where(' in code,
        'mask' in code,
        'boolean' in code
    ]
    
    has_explicit_loop = 'for ' in code and 'in range(' in code
    has_vectorization_signs = any(vectorization_indicators)
    
    # Student passes vectorization check if they have vectorization indicators and no explicit for loop
    attempted_vectorization = has_vectorization_signs and not has_explicit_loop
    
    return code_works and attempted_vectorization