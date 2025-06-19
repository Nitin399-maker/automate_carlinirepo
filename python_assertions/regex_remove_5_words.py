import subprocess
import tempfile
import os
import re

def assert_regex_function(response, context=None):
    """
    Promptfoo assertion that evaluates a Python regex function implementation.
    Extracts code, runs test cases, and checks for expected outputs.
    """
    
    # Test cases and expected answers
    test_cases = [
        ("match('hi hi hi hi hi')", '"hi"'),
        ("match('hi hi hi hi')", '""'),
        ("match('hello this is is is is is a test')", '"is"')
    ]
    
    # Step 1: Extract code from response
    def extract_code(text):
        # Remove language specifiers from code blocks
        text = re.sub(r'```[a-z]*', '```', text)
        
        if "```" in text and text.count("```") >= 2:
            # Extract code from markdown blocks
            parts = text.split("```")
            if len(parts) >= 2:
                return parts[1].strip()
        
        # If no code blocks found, assume the entire response is code
        return text.strip()
    
    code = extract_code(response)
    
    if not code:
        return {
            "pass": False,
            "score": 0,
            "reason": "No code found in response"
        }
    
    # Step 2: Prepare test execution code
    test_code = ""
    for test_call, expected in test_cases:
        test_code += f"print(repr({test_call}))\n"
    
    full_code = code + "\n\n" + test_code
    
    # Step 3: Run Python code with test cases
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(full_code)
            temp_file = f.name
        
        result = subprocess.run(
            ['python', temp_file],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        os.unlink(temp_file)
        
        if result.returncode != 0:
            return {
                "pass": False,
                "score": 0,
                "reason": f"Code execution failed: {result.stderr}"
            }
        
        output = result.stdout.strip()
        
    except subprocess.TimeoutExpired:
        return {
            "pass": False,
            "score": 0,
            "reason": "Code execution timed out"
        }
    except Exception as e:
        return {
            "pass": False,
            "score": 0,
            "reason": f"Error running code: {str(e)}"
        }
    
    # Step 4: Evaluate output against expected results
    output_lines = output.strip().split('\n')
    expected_outputs = [expected for _, expected in test_cases]
    
    if len(output_lines) != len(expected_outputs):
        return {
            "pass": False,
            "score": 0,
            "reason": f"Expected {len(expected_outputs)} outputs, got {len(output_lines)}"
        }
    
    passed_tests = 0
    for i, (actual, expected) in enumerate(zip(output_lines, expected_outputs)):
        if expected in actual:
            passed_tests += 1
    
    score = passed_tests / len(test_cases)
    is_passing = score == 1.0
    
    return {
        "pass": is_passing,
        "score": score,
        "reason": f"Passed {passed_tests}/{len(test_cases)} test cases. Output: {output}"
    }