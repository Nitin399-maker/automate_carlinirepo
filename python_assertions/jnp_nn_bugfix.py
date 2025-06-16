import re
import subprocess
import tempfile
import os

def get_assertion(response, context=None):
    """
    Evaluates if the LLM response correctly fixes the JAX numpy bug.
    Expected to return a dict with pass/fail status and score.
    """
    
    # Extract code from response
    code = extract_code_from_response(response)
    if not code:
        return {
            "pass": False,
            "score": 0,
            "reason": "No valid code found in response"
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
    
    # Check if output contains expected substrings indicating correct sums close to 1.0
    success = check_output_for_success(output)
    
    return {
        "pass": success,
        "score": 1 if success else 0,
        "reason": f"Output: {output}" if success else f"Expected sums close to 1.0, got: {output}"
    }

def extract_code_from_response(response):
    """Extract and prepare code from LLM response for execution."""
    # Remove language specifiers from code blocks
    response = re.sub(r'```[a-z]*', '```', response)
    
    if "```" in response:
        # Extract code from markdown code blocks
        parts = response.split("```")
        if len(parts) >= 2:
            code = parts[1]
        else:
            code = response
    else:
        code = response
    
    # Basic cleanup
    code = code.strip()
    
    # Ensure we have the imports and main execution
    if "import jax" not in code:
        return None
    
    return code

def run_python_code(code):
    """Execute Python code and return output."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_file = f.name
    
    try:
        result = subprocess.run(
            ['python', temp_file],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            raise Exception(f"Execution error: {result.stderr}")
        
        return result.stdout.strip()
    
    finally:
        os.unlink(temp_file)

def check_output_for_success(output):
    """Check if output contains substrings indicating correct softmax sums."""
    target_substrings = ["1.0,", "1.00000", "1.0 ", "0.99999"]
    
    for substr in target_substrings:
        if substr in output:
            return True
    
    return False