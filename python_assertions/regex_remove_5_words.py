import re
import subprocess
import tempfile
import os

def check_regex_function(response, context=None):
    """
    Promptfoo assertion function that evaluates if the LLM response contains
    a correct Python function for regex matching repeated words.
    """
    
    # Step 1: Extract code from response (equivalent to ExtractCode)
    def extract_code(output):
        # Remove language specifiers from code blocks
        output = re.sub('```[a-z]*', '```', output)
        
        if "```" in output and output.count("```") >= 2:
            # Extract code between first pair of triple backticks
            parts = output.split("```")
            if len(parts) >= 2:
                return parts[1].strip()
        
        # If no code blocks found, treat entire output as code
        return output.strip()
    
    # Step 2: Create test case (equivalent to PythonRun)
    test_case = '''
# Test the match function
print(repr(match('hi hi hi hi hi')))
print(repr(match('hi hi hi hi')))
print(repr(match('hello this is is is is is a test')))
'''
    
    # Expected output (equivalent to SubstringEvaluator)
    expected_output = '"hi"\n""\n"is"'
    
    try:
        # Extract the code
        extracted_code = extract_code(response)
        
        # Combine code with test case
        full_code = extracted_code + "\n\n" + test_case
        
        # Step 3: Run the Python code using subprocess
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(full_code)
            temp_file = f.name
        
        try:
            # Execute the code
            result = subprocess.run(
                ['python', temp_file],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return {
                    'pass': False,
                    'score': 0,
                    'reason': f'Code execution failed: {result.stderr}'
                }
            
            # Step 4: Evaluate output (equivalent to SubstringEvaluator)
            actual_output = result.stdout.strip()
            
            # Check if the expected output is contained in actual output
            if expected_output in actual_output:
                return {
                    'pass': True,
                    'score': 1,
                    'reason': 'Function correctly identifies repeated words'
                }
            else:
                return {
                    'pass': False,
                    'score': 0,
                    'reason': f'Expected output "{expected_output}" not found in "{actual_output}"'
                }
                
        finally:
            # Clean up temp file
            if os.path.exists(temp_file):
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
            'reason': f'Error during evaluation: {str(e)}'
        }