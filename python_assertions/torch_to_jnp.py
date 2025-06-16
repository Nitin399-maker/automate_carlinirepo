import subprocess
import tempfile
import re
import os

def get_assertion(response, context=None):
    """
    Evaluates if the response contains valid JAX code that:
    1. Does not import torch
    2. When executed, produces output containing softmax probabilities (sum to 1.0)
    """
    
    # Extract code from response
    code = extract_code_from_response(response)
    if not code:
        return {
            "pass": False,
            "score": 0,
            "reason": "No code found in response"
        }
    
    # Check that torch is not imported
    if "import torch" in code:
        return {
            "pass": False,
            "score": 0,
            "reason": "Code still imports torch - should be pure JAX"
        }
    
    # Execute the code and check output
    try:
        output = run_python_code(code)
        
        # Check if output contains values indicating softmax (probabilities sum to 1.0)
        success_patterns = ["1.0,", "1.00000", "1.0 ", "0.99999"]
        has_valid_output = any(pattern in output for pattern in success_patterns)
        
        if has_valid_output:
            return {
                "pass": True,
                "score": 1,
                "reason": "Code successfully converts PyTorch to JAX and produces correct softmax output"
            }
        else:
            return {
                "pass": False,
                "score": 0,
                "reason": f"Code executes but doesn't produce expected softmax output. Got: {output[:200]}"
            }
            
    except Exception as e:
        return {
            "pass": False,
            "score": 0,
            "reason": f"Code execution failed: {str(e)}"
        }

def extract_code_from_response(response):
    """Extract code from markdown code blocks or return the response as-is"""
    # Remove language specifiers from code blocks
    response = re.sub(r'```[a-z]*', '```', response)
    
    if "```" in response and response.count("```") >= 2:
        # Extract code between first pair of ```
        parts = response.split("```")
        if len(parts) >= 2:
            return parts[1].strip()
    
    # If no code blocks found, return the whole response
    return response.strip()

def run_python_code(code):
    """Execute Python code using subprocess and return output"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        f.flush()
        
        try:
            result = subprocess.run(
                ['python', f.name],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise Exception(f"Code execution failed with error: {result.stderr}")
            
            return result.stdout
            
        finally:
            os.unlink(f.name)