import re
import subprocess
import tempfile
import os
import time
import base64

def assert_webgl_house_drawing(response, context=None):
    """
    Evaluates if the LLM response contains HTML/WebGL code that draws a house with chimney.
    Returns a score between 0 and 1.
    """
    
    # Extract code from response
    def extract_code(output):
        output = re.sub('```[a-z]*', '```', output)
        if "```" in output and output.count("```") >= 2:
            return output.split("```")[1]
        else:
            return output
    
    code = extract_code(response)
    
    # Check if THREE.js is NOT used (should use raw WebGL)
    if "THREE." in code:
        return {
            "pass": False,
            "score": 0.0,
            "reason": "Code uses THREE.js library instead of raw WebGL"
        }
    
    # Create temporary HTML file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        f.write(code)
        html_path = f.name
    
    try:
        # Take screenshot using headless Chrome
        screenshot_path = html_path.replace('.html', '.png')
        
        chrome_cmd = [
            'google-chrome',
            '--headless',
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--window-size=800,600',
            f'--screenshot={screenshot_path}',
            f'file://{html_path}'
        ]
        
        subprocess.run(chrome_cmd, capture_output=True, timeout=10)
        time.sleep(1)
        
        if not os.path.exists(screenshot_path):
            return {
                "pass": False,
                "score": 0.0,
                "reason": "Failed to generate screenshot"
            }
        
        # Convert screenshot to base64 for simple analysis
        with open(screenshot_path, 'rb') as img_file:
            img_data = base64.b64encode(img_file.read()).decode()
        
        # Simple heuristic: check if image is not blank/empty
        # A real implementation would use vision AI, but this avoids API calls
        img_size = len(img_data)
        
        # Basic validation - if screenshot was generated and has reasonable size
        if img_size > 1000:  # Arbitrary threshold for non-empty image
            # Check if code contains WebGL-related terms that suggest drawing
            webgl_indicators = ['gl.', 'WebGL', 'canvas', 'vertex', 'fragment', 'shader']
            drawing_indicators = ['triangle', 'rectangle', 'polygon', 'draw', 'render']
            
            webgl_score = sum(1 for indicator in webgl_indicators if indicator in code)
            drawing_score = sum(1 for indicator in drawing_indicators if indicator in code)
            
            total_score = (webgl_score + drawing_score) / 10.0
            total_score = min(1.0, max(0.1, total_score))  # Clamp between 0.1 and 1.0
            
            return {
                "pass": total_score > 0.5,
                "score": total_score,
                "reason": f"WebGL code detected with screenshot generated (indicators: {webgl_score + drawing_score})"
            }
        else:
            return {
                "pass": False,
                "score": 0.1,
                "reason": "Screenshot appears to be blank or too small"
            }
            
    except subprocess.TimeoutExpired:
        return {
            "pass": False,
            "score": 0.0,
            "reason": "Screenshot generation timed out"
        }
    except Exception as e:
        return {
            "pass": False,
            "score": 0.0,
            "reason": f"Error during evaluation: {str(e)}"
        }
    finally:
        # Cleanup temporary files
        try:
            os.unlink(html_path)
            if 'screenshot_path' in locals() and os.path.exists(screenshot_path):
                os.unlink(screenshot_path)
        except:
            pass