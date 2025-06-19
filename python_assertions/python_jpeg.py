import subprocess
import tempfile
import os
import re
import json
import io
from PIL import Image

def assert_red_triangle_gif(response, context=None):
    """
    Evaluates if the response contains code that generates a GIF with a red triangle.
    """
    
    # Extract code from response
    code = extract_code_from_response(response)
    if not code:
        return {
            'pass': False,
            'score': 0,
            'reason': 'No code found in response'
        }
    
    # Run the Python code and capture output
    try:
        gif_bytes = run_python_code(code)
        if not gif_bytes:
            return {
                'pass': False,
                'score': 0,
                'reason': 'Code execution failed or produced no output'
            }
    except Exception as e:
        return {
            'pass': False,
            'score': 0,
            'reason': f'Code execution error: {str(e)}'
        }
    
    # Analyze the image using vision LLM
    try:
        description = analyze_image_with_llm(gif_bytes)
    except Exception as e:
        return {
            'pass': False,
            'score': 0,
            'reason': f'Image analysis failed: {str(e)}'
        }
    
    # Check if description contains both "triangle" and "red"
    has_triangle = "triangle" in description.lower()
    has_red = "red" in description.lower()
    
    if has_triangle and has_red:
        return {
            'pass': True,
            'score': 1,
            'reason': f'Successfully generated red triangle. Description: {description}'
        }
    else:
        return {
            'pass': False,
            'score': 0,
            'reason': f'Missing required elements. Has triangle: {has_triangle}, Has red: {has_red}. Description: {description}'
        }


def extract_code_from_response(response):
    """Extract Python code from the response, keeping main function if present."""
    # Remove language identifiers from code blocks
    response = re.sub(r'```[a-z]*', '```', response)
    
    # Try to extract from code blocks first
    if response.count("```") >= 2:
        code = response.split("```")[1]
        return code.strip()
    
    # If no clear code blocks, use LLM to extract complete runnable code
    if "```" not in response or response.count("```") != 2:
        code = extract_complete_code_with_llm(response)
        return code
    
    return response.strip()


def extract_complete_code_with_llm(response):
    """Use LLM to extract complete runnable code."""
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImRpdnlhbnNoYS5zaHJlZUBzdHJhaXZlLmNvbSJ9.RBtDprvolLLQb-gCqfchd8ezK83Uo9Z3m5AjFAQLNgY"
    if not token:
        # Fallback to simple extraction if no token available
        return response
    
    prompt = f"""Take the below answer to my programming question and return just the complete code in a single file so I can copy and paste it into an editor and directly run it. Include any header and main necessary so I can run it by copying this one file. DO NOT MODIFY THE CODE OR WRITE NEW CODE. Here is the code:
{response}"""
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        result = subprocess.run([
            'curl', '-X', 'POST', 
            'https://llmfoundry.straive.com/openai/v1/chat/completions',
            '-H', f'Authorization: Bearer {token}:my-test-project',
            '-H', 'Content-Type: application/json',
            '-d', json.dumps(payload)
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            llm_response = json.loads(result.stdout)
            extracted = llm_response['choices'][0]['message']['content']
            
            # Extract code from the LLM response
            extracted = re.sub(r'```[a-z]*', '```', extracted)
            if "```" in extracted:
                return extracted.split("```")[1].strip()
            return extracted.strip()
    except:
        pass
    
    # Fallback to original response
    return response


def run_python_code(code):
    """Run Python code and capture binary output."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_file = f.name
    
    try:
        result = subprocess.run([
            'python3', temp_file
        ], capture_output=True, timeout=30)
        
        if result.returncode == 0:
            return result.stdout
        else:
            raise Exception(f"Python execution failed: {result.stderr.decode()}")
    
    finally:
        os.unlink(temp_file)


def analyze_image_with_llm(image_bytes):
    """Analyze image using vision LLM to describe shapes and colors."""
    token = os.environ.get('LLMFOUNDRY_TOKEN')
    if not token:
        raise Exception("LLMFOUNDRY_TOKEN environment variable not set")
    
    # Convert image bytes to base64 for API call
    import base64
    
    # Save bytes to temporary file and convert to base64
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.gif', delete=False) as f:
        f.write(image_bytes)
        temp_image = f.name
    
    try:
        # Read and encode image
        with open(temp_image, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode()
        
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Describe the shapes in this image and their color"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/gif;base64,{image_data}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 512
        }
        
        result = subprocess.run([
            'curl', '-X', 'POST', 
            'https://llmfoundry.straive.com/openai/v1/chat/completions',
            '-H', f'Authorization: Bearer {token}:my-test-project',
            '-H', 'Content-Type: application/json',
            '-d', json.dumps(payload)
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            response = json.loads(result.stdout)
            return response['choices'][0]['message']['content']
        else:
            raise Exception(f"Vision API call failed: {result.stderr}")
    
    finally:
        os.unlink(temp_image)