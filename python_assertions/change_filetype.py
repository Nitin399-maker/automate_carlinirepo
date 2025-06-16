import subprocess
import tempfile
import os
import re
from PIL import Image
import numpy as np

def check_image_elf_conversion(response, context=None):
    """
    Evaluates if the LLM response contains code that can modify a PNG file
    to be detected as an ELF executable while remaining a valid image.
    """
    
    # Setup: Create test image
    def setup_image():
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        img[0, 0] = [255, 0, 0]
        img[0, 1] = [0, 255, 0]
        img[0, 2] = [0, 0, 255]
        Image.fromarray(img).save("image.png")
    
    # Test function
    def test_ok():
        if 'ELF' not in subprocess.getoutput("file image.png"):
            return False
        img = np.array(Image.open("image.png"))
        return (img[0, 0].tolist() == [255, 0, 0] and 
                img[0, 1].tolist() == [0, 255, 0] and 
                img[0, 2].tolist() == [0, 0, 255] and 
                img.shape == (100, 100, 3))
    
    # Extract code from response
    def extract_code(output):
        output = re.sub('```[a-z]*', '```', output)
        if "```" in output and output.count("```") >= 2:
            return output.split("```")[1]
        return output
    
    with tempfile.TemporaryDirectory() as temp_dir:
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Setup test image
            setup_image()
            
            # Extract and run the code
            code = extract_code(response)
            
            # Write code to file and execute
            with open("solution.py", "w") as f:
                f.write(code)
            
            # Run the solution
            result = subprocess.run(["python", "solution.py"], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return {
                    "pass": False,
                    "score": 0.0,
                    "reason": f"Code execution failed: {result.stderr}"
                }
            
            # Test the result
            success = test_ok()
            
            return {
                "pass": success,
                "score": 1.0 if success else 0.0,
                "reason": "Successfully converted PNG to appear as ELF while maintaining image functionality" if success else "Failed to properly convert image"
            }
            
        except Exception as e:
            return {
                "pass": False,
                "score": 0.0,
                "reason": f"Error during evaluation: {str(e)}"
            }
        finally:
            os.chdir(old_cwd)