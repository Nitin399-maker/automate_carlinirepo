import re
import subprocess
import tempfile
import os

def assert_hello_world_program(response, context=None):
    """
    Evaluates if the model response contains a Python program that prints "hello world"
    """
    try:
        # Extract code from response
        code = extract_code_from_response(response, keep_main=True)
        if not code:
            return {
                "pass": False,
                "score": 0,
                "reason": "No code found in response"
            }
        
        # Run the Python code
        output = run_python_code(code)
        if output is None:
            return {
                "pass": False,
                "score": 0,
                "reason": "Code execution failed"
            }
        
        # Check if output contains "hello world"
        target = "hello world"
        if target in output.lower():
            return {
                "pass": True,
                "score": 1,
                "reason": f"Code successfully printed '{target}'"
            }
        else:
            return {
                "pass": False,
                "score": 0,
                "reason": f"Expected '{target}' in output, got: {output.strip()}"
            }
            
    except Exception as e:
        return {
            "pass": False,
            "score": 0,
            "reason": f"Evaluation error: {str(e)}"
        }

def extract_code_from_response(response, keep_main=True):
    """Extract Python code from the LLM response"""
    # Clean up code block markers
    response = re.sub(r'```[a-z]*', '```', response)
    
    # Try to extract code between triple backticks
    if "```" in response and response.count("```") >= 2:
        parts = response.split("```")
        if len(parts) >= 3:
            code = parts[1].strip()
            # Remove language identifier if present
            lines = code.split('\n')
            if lines and lines[0].strip() in ['python', 'py']:
                code = '\n'.join(lines[1:])
            return code
    
    # If no code blocks found, treat entire response as potential code
    # Look for lines that look like Python code
    lines = response.split('\n')
    code_lines = []
    found_code = False
    
    for line in lines:
        stripped = line.strip()
        if (stripped.startswith('print(') or 
            stripped.startswith('def ') or 
            stripped.startswith('import ') or 
            stripped.startswith('from ') or
            'print(' in stripped):
            found_code = True
            code_lines.append(line)
        elif found_code and stripped and not stripped.startswith('#'):
            code_lines.append(line)
        elif found_code and not stripped:
            code_lines.append(line)
    
    if code_lines:
        return '\n'.join(code_lines)
    
    return response.strip()

def run_python_code(code):
    """Run Python code using subprocess and return output"""
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # Run the Python code
            result = subprocess.run(
                ['python', temp_file],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return result.stdout
            else:
                return None
                
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file):
                os.unlink(temp_file)
                
    except Exception:
        return None