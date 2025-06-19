import re
import subprocess
import tempfile
import os

def get_assertion(response, context=None):
    """
    Evaluates if the model can identify and fix a JAX numpy function bug.
    Expects the response to contain corrected code that produces softmax outputs summing to 1.0.
    """
    
    # Extract code from response
    code = extract_code_from_response(response)
    if not code:
        return {
            "pass": False,
            "score": 0,
            "reason": "No code found in response"
        }
    
    # Run the extracted code
    try:
        output = run_python_code(code)
    except Exception as e:
        return {
            "pass": False,
            "score": 0,
            "reason": f"Code execution failed: {str(e)}"
        }
    
    # Check if output contains expected values (softmax sums close to 1.0)
    target_substrings = ["1.0,", "1.00000", "1.0 ", "0.99999"]
    
    for substr in target_substrings:
        if substr in output:
            return {
                "pass": True,
                "score": 1,
                "reason": f"Found expected output pattern: {substr}"
            }
    
    return {
        "pass": False,
        "score": 0,
        "reason": f"Output did not contain expected patterns. Got: {output[:200]}..."
    }

def extract_code_from_response(response):
    """Extract code from response, handling code blocks and ensuring it's runnable."""
    
    # Clean up code block markers
    response = re.sub(r'```[a-z]*', '```', response)
    
    # Try to extract from code blocks first
    if response.count("```") >= 2:
        code_blocks = response.split("```")
        for i in range(1, len(code_blocks), 2):
            code = code_blocks[i].strip()
            if code and "import" in code:
                return code
    
    # If no code blocks, try to extract code from the entire response
    # Look for Python imports as indicators of code
    lines = response.split('\n')
    code_lines = []
    in_code = False
    
    for line in lines:
        if any(keyword in line for keyword in ['import ', 'def ', 'class ', 'if __name__']):
            in_code = True
        if in_code:
            # Remove or replace problematic Unicode characters
            line = line.encode('ascii', 'ignore').decode('ascii')
            code_lines.append(line)
    
    if code_lines:
        return '\n'.join(code_lines)
    
    # Fallback: return the response as-is if it looks like code
    if any(keyword in response for keyword in ['import', 'def', 'jnp', 'jax']):
        # Remove or replace problematic Unicode characters
        return response.encode('ascii', 'ignore').decode('ascii')
    
    return None

def run_python_code(code):
    """Run Python code and return the output."""
    
    # Create a temporary file with UTF-8 encoding
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(code)
        temp_file = f.name
    
    try:
        # Run the code with UTF-8 encoding for both input and output
        result = subprocess.run(
            ['python', temp_file],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',  # This will ignore any characters that can't be decoded
            timeout=30
        )
        
        if result.returncode != 0:
            raise Exception(f"Code execution failed with return code {result.returncode}. Error: {result.stderr}")
        
        return result.stdout
        
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file):
            os.unlink(temp_file)