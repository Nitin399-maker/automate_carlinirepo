import subprocess
import tempfile
import os
import re
import sys

def get_assertion(response, context=None):
    # Setup: Create run_tokenizer.py
    code = """import re

class Tokenizer:
    def __init__(self, input_str):
        '''
        input_str: a string of digits and operators
        '''
        self.position = 0
        self.tokens = re.findall(r'\d+|(\+|\-|\*|/|sin|cos|\(|\))', input_str)

    def get_next_token(self):
        if self.position >= len(self.tokens):
            return None
        token = self.tokens[self.position]
        self.position += 1
        return token

    def peek_next_token(self):
        if self.position >= len(self.tokens):
            return None
        return self.tokens[self.position]"""
    
    with open('run_tokenizer.py', 'w') as f:
        f.write(code)
    
    # ExtractCode: Extract patch from response
    patch_content = response
    if "```" in response:
        # Handle code blocks
        response = re.sub('```[a-z]*', '```', response)
        if response.count("```") >= 2:
            patch_content = response.split("```")[1]
    
    # MakeFile: Create fix.patch
    with open('fix.patch', 'w') as f:
        f.write(patch_content)
    
    # Apply patch
    try:
        result = subprocess.run(['patch'], stdin=open('fix.patch', 'r'), 
                              capture_output=True, text=True)
        if result.returncode != 0:
            return {
                "pass": False,
                "score": 0,
                "reason": f"Patch failed to apply: {result.stderr}"
            }
    except Exception as e:
        return {
            "pass": False,
            "score": 0,
            "reason": f"Error applying patch: {str(e)}"
        }
    
    # PyEvaluator: Check if tokenizer works correctly
    try:
        # Import the patched module
        if 'run_tokenizer' in sys.modules:
            del sys.modules['run_tokenizer']
        import run_tokenizer
        
        tokenizer = run_tokenizer.Tokenizer("cos(1)+sin(23)*5")
        expected = ['cos', '(', '1', ')', '+', 'sin', '(', '23', ')', '*', '5']
        actual = tokenizer.tokens
        
        if actual == expected:
            return {"pass": True, "score": 1}
        else:
            return {
                "pass": False,
                "score": 0,
                "reason": f"Tokenizer output incorrect. Expected: {expected}, Got: {actual}"
            }
    except Exception as e:
        return {
            "pass": False,
            "score": 0,
            "reason": f"Error running tokenizer: {str(e)}"
        }
    finally:
        # Cleanup
        for file in ['run_tokenizer.py', 'fix.patch']:
            if os.path.exists(file):
                os.remove(file)