import re
import subprocess
import tempfile
import os

def assert_tree_creation(response, context=None):
    """
    Promptfoo assertion to test if the model can create a tree from a string.
    Expects the response to contain Python code that prints: (1 (2 (3 4 5 6) (7 8)) (9 10 (11 12)))
    """
    
    def extract_code(text):
        # Remove language specifiers from code blocks
        text = re.sub(r'```[a-z]*', '```', text)
        
        if "```" in text and text.count("```") >= 2:
            # Extract code from markdown blocks
            code = text.split("```")[1]
        else:
            # Use the entire response as code
            code = text
        
        return code.strip()
    
    def run_python_code(code):
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
            return result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            return "", "Timeout expired", 1
        except Exception as e:
            return "", str(e), 1
        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_file)
            except:
                pass
    
    # Extract code from the response
    extracted_code = extract_code(response)
    
    if not extracted_code:
        return {
            "pass": False,
            "score": 0.0,
            "reason": "No code found in response"
        }
    
    # Run the extracted code
    stdout, stderr, returncode = run_python_code(extracted_code)
    
    if returncode != 0:
        return {
            "pass": False,
            "score": 0.0,
            "reason": f"Code execution failed: {stderr}"
        }
    
    # Check if the expected output is in the stdout
    expected_output = "(1 (2 (3 4 5 6) (7 8)) (9 10 (11 12)))"
    
    if expected_output in stdout:
        return {
            "pass": True,
            "score": 1.0,
            "reason": "Code successfully generated the expected tree output"
        }
    else:
        return {
            "pass": False,
            "score": 0.0,
            "reason": f"Expected output not found. Got: {stdout.strip()}"
        }