import re
import subprocess
import tempfile
import os

def assert_dataflow_dsl(response, context=None):
    """
    Evaluates if the model can generate a python program that defines dataflow DSL.
    Expected to work with: Const(2) >> Square() >> Inc() >> Square() >> Square() >> Print()
    Should output 625.
    """
    
    # Extract code from response
    def extract_code(output):
        output = re.sub('```[a-z]*', '```', output)
        if "```" in output and output.count("```") >= 2:
            return output.split("```")[1]
        else:
            return output
    
    code = extract_code(response)
    
    # Test case
    test_case = "Const(2) >> Square() >> Inc() >> Square() >> Square() >> Print()"
    
    # Combine code with test case
    full_code = code + "\n\n" + test_case
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(full_code)
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
        
        # Check if output contains "625"
        if "625" in output:
            return {
                "pass": True,
                "score": 1.0,
                "reason": f"Code executed successfully and produced expected output: {output.strip()}"
            }
        else:
            return {
                "pass": False,
                "score": 0.0,
                "reason": f"Code executed but didn't produce expected output '625'. Got: {output.strip()}"
            }
            
    except subprocess.TimeoutExpired:
        return {
            "pass": False,
            "score": 0.0,
            "reason": "Code execution timed out"
        }
    except Exception as e:
        return {
            "pass": False,
            "score": 0.0,
            "reason": f"Code execution failed: {str(e)}"
        }
    finally:
        # Clean up temporary file
        if os.path.exists(temp_file):
            os.unlink(temp_file)