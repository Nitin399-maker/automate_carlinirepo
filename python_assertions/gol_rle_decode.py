import subprocess
import tempfile
import os
import re

def assert_rle_decode(response, context=None):
    """
    Evaluates if the LLM response correctly implements RLE to numpy array conversion.
    """
    
    # Extract code from response
    code = extract_code_from_response(response)
    if not code:
        return {
            'pass': False,
            'score': 0,
            'reason': 'No code found in response'
        }
    
    # Test case and expected answer
    rle = """16b2o3b2o$2o$2o$19b2o$17b5o$21bo$17b3o$o16bo$o17b2o$bo16b2o$b2o$3bo$o17b2o3b2o$2b2o14bobobobo$11bobo5b5o$11b2o7b3o$2o10bo8bo$b2o$b2o2$2o$bo2$6bobo$2o3bo$bo3bo$o4bo2bo7bo$5b3o7b2o7bo$15bobo5b3o$22b5o$21b2o3b2o$22b5o$22b5o$14b2o6bo2bo$14bobo4bo3bo$11b2obobo4bo$11bobobo5bob2o$13bo8bo$4bobo6b2o$7bo5b3o50bo$7bo5b3o3b2o3b2o40b4o$4bo2bo5b3o3bo5bo41b4o$5b3o5b2o35bo16bo2bo$13bo6bo3bo24bobo15b4o4b2o$11bobobo5b3o15b2o7bob2o14b4o5b2o$11b2obobo21bobo6b2ob2o14bo8b2o$14bobo20bo6b3obob2o$14b2o12b2o7bo2bo2bo2bo2bobo$28b2o7bo6b2o4bo16bobo$38bobo26b2o$39b2o27bo4b2o$21b2o49bo2bo$21b2o28bobo18b3o$52b2o21b2o$52bo21bo$74b2o$59bo$62bo$59bo14bo$62bo$61bob3o8bo$59b4o2bo9b2o$64bo$52bo$51b2o$40b2o8b2o4b2o5bo$40b2o7b3o4b2o3bobo$50b2o4b2o2bobo11b2o$4bobo44b2o6bo2bo11b2o$7bo44bo7bobo$o6bo53bobo$o3bo2bo55bo$5b3o5$4b4o$3bo3bo$7bo$3bo2bo3$o2b3o2b2o$2b5o2bo64b3o$9o67bo$9b3o63bo$o7bo2bo$9b2o3$4b2o$o3b3o$o5b2obo5b2o$bo4bo2bo5b2o$2o4b2obo$o3b3o$4b2o2$59b3o12b2o$61bo12b2o!"""
    
    test_case = f"""
import numpy as np
result = (np.array(rle_to_arr('''{rle}''', 101, 77), dtype=np.uint32).flatten() * np.arange(77*101)).sum()
print(result)
"""
    
    expected_answer = "1563304"
    
    # Run the code with test case
    full_code = code + "\n\n" + test_case
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(full_code)
            temp_file = f.name
        
        result = subprocess.run(
            ['python3', temp_file],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        os.unlink(temp_file)
        
        if result.returncode != 0:
            return {
                'pass': False,
                'score': 0,
                'reason': f'Code execution failed with error: {result.stderr}'
            }
        
        output = result.stdout.strip()
        
        # Check if expected answer is in output
        if expected_answer in output:
            return {
                'pass': True,
                'score': 1,
                'reason': f'Correct output found: {expected_answer}'
            }
        else:
            return {
                'pass': False,
                'score': 0,
                'reason': f'Expected {expected_answer}, got output: {output}'
            }
            
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
            'reason': f'Execution error: {str(e)}'
        }


def extract_code_from_response(response):
    """
    Extract code from LLM response, handling code blocks and raw code.
    """
    # Remove language specifiers from code blocks
    cleaned_response = re.sub(r'```[a-z]*', '```', response)
    
    # If there are exactly 2 backticks (one opening, one closing code block)
    if cleaned_response.count("```") == 2:
        try:
            code = cleaned_response.split("```")[1]
            return code.strip()
        except IndexError:
            pass
    
    # If no clear code blocks, return the whole response
    return response.strip()