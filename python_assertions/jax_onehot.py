import re
import subprocess
import tempfile
import os
import sys

def check_jax_one_hot(response, context=None):
    """
    Evaluates if the response contains a correct one-hot function implementation
    using numpy instead of JAX for testing.
    """
    
    def extract_code(output):
        # Remove language specifiers from code blocks
        output = re.sub('```[a-z]*', '```', output)
        if "```" in output and output.count("```") >= 2:
            code = output.split("```")[1]
        else:
            code = output
        return code.strip()
    
    # Step 1: Extract and modify code to use numpy
    extracted_code = extract_code(response)
    modified_code = (extracted_code
                    .replace('import jax.numpy as jnp', 'import numpy as np')
                    .replace('jax.numpy', 'numpy')
                    .replace('jnp', 'np'))
    
    # Step 2: Prepare test case with numpy
    test_case = """
import numpy as np

# Test cases
test_cases = [
    (np.array([1,2,0]), 5),
    (np.array([0,1,2,3]), 4),
    (np.array([2]), 3)
]

for x, num_classes in test_cases:
    result = one_hot(x, num_classes)
    print(f"Input: {x}, num_classes: {num_classes}")
    print(f"Output:\\n{result}\\n")
"""
    
    # Step 3: Combine code
    full_code = """# -*- coding: utf-8 -*-
import numpy as np

""" + modified_code + "\n\n" + test_case
    
    # Step 4: Run the code
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', encoding='utf-8', delete=False) as f:
            f.write(full_code)
            temp_file = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=30
            )
            
            if result.returncode != 0:
                return {
                    'pass': False,
                    'score': 0,
                    'reason': f'Code execution failed: {result.stderr}'
                }
            
            output = result.stdout.strip()
            
        finally:
            if os.path.exists(temp_file):
                try:
                    os.close(os.open(temp_file, os.O_RDONLY))
                    os.unlink(temp_file)
                except:
                    pass
        
        # Step 5: Check results
        expected_patterns = [
            # First test case
            r"\[\[0\.\s+1\.\s+0\.\s+0\.\s+0\.\]\s*\[0\.\s+0\.\s+1\.\s+0\.\s+0\.\]\s*\[1\.\s+0\.\s+0\.\s+0\.\s+0\.\]\s*\]",
            # Second test case
            r"\[\[1\.\s+0\.\s+0\.\s+0\.\]\s*\[0\.\s+1\.\s+0\.\s+0\.\]\s*\[0\.\s+0\.\s+1\.\s+0\.\]\s*\[0\.\s+0\.\s+0\.\s+1\.\]\s*\]",
            # Third test case
            r"\[\[0\.\s+0\.\s+1\.\]\s*\]"
        ]
        
        # Count how many patterns match
        matches = sum(1 for pattern in expected_patterns 
                     if re.search(pattern, output.replace('\n', ' ')))
        
        if matches == len(expected_patterns):
            return {
                'pass': True,
                'score': 1.0,
                'reason': 'All test cases passed successfully'
            }
        elif matches > 0:
            return {
                'pass': False,
                'score': matches / len(expected_patterns),
                'reason': f'{matches} out of {len(expected_patterns)} test cases passed'
            }
        else:
            return {
                'pass': False,
                'score': 0,
                'reason': f'No test cases passed. Output:\n{output}'
            }
            
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