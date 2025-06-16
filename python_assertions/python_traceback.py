import subprocess
import tempfile
import os
import re

def assert_traceback_fix(response, context=None):
    """
    Evaluates if the model can fix a Python traceback handling program.
    Expects the response to contain fixed code that outputs "x: 5" and "y: 6".
    """
    
    # Extract code from response (similar to ExtractCode)
    def extract_code(output):
        # Remove language specifiers from code blocks
        output = re.sub('```[a-z]*', '```', output)
        
        if "```" in output and output.count("```") >= 2:
            # Extract code between first pair of triple backticks
            parts = output.split("```")
            if len(parts) >= 3:
                return parts[1].strip()
        
        # If no code blocks found, assume entire response is code
        return output.strip()
    
    try:
        # Extract the code
        code = extract_code(response)
        
        if not code:
            return {
                'pass': False,
                'score': 0,
                'reason': 'No code found in response'
            }
        
        # Create temporary file
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
            
            output = result.stdout
            
            # Check if both required substrings are present
            has_x_5 = "x: 5" in output
            has_y_6 = "y: 6" in output
            
            success = has_x_5 and has_y_6
            
            if success:
                return {
                    'pass': True,
                    'score': 1,
                    'reason': 'Code successfully fixed and outputs correct variables'
                }
            else:
                missing = []
                if not has_x_5:
                    missing.append("x: 5")
                if not has_y_6:
                    missing.append("y: 6")
                
                return {
                    'pass': False,
                    'score': 0,
                    'reason': f'Missing expected output: {", ".join(missing)}. Got: {repr(output)}'
                }
                
        finally:
            # Clean up temporary file
            os.unlink(temp_file)
            
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
            'reason': f'Error executing code: {str(e)}'
        }