import re
import subprocess
import tempfile
import os
from PIL import Image
import io

def assert_flag_draw_bmp(response, context=None):
    """
    Evaluates if the response contains C code that generates an American flag BMP image.
    
    Args:
        response: The LLM response containing C code
        context: Additional context (unused)
    
    Returns:
        dict: Pass/fail result with details
    """
    
    try:
        # Step 1: Extract C code from response
        code = extract_c_code(response)
        if not code:
            return {
                "pass": False,
                "score": 0,
                "reason": "No C code found in response"
            }
        
        # Step 2: Compile and run C code to get BMP output
        bmp_bytes = compile_and_run_c_code(code)
        if not bmp_bytes:
            return {
                "pass": False,
                "score": 0,
                "reason": "Failed to compile or run C code"
            }
        
        # Step 3: Validate BMP format and check if it's an image
        try:
            img = Image.open(io.BytesIO(bmp_bytes))
            img.verify()  # Verify it's a valid image
        except Exception as e:
            return {
                "pass": False,
                "score": 0,
                "reason": f"Generated output is not a valid BMP image: {str(e)}"
            }
        
        # Step 4: Check if the image appears to be an American flag
        # Since we're avoiding LLM calls, we'll do basic validation:
        # - Check if it's a valid BMP
        # - Has reasonable dimensions for a flag
        # - Has appropriate color patterns (red, white, blue dominant)
        img = Image.open(io.BytesIO(bmp_bytes))
        width, height = img.size
        
        # Basic flag dimension check (width should be roughly 1.9x height for US flag)
        if width < 50 or height < 25:
            return {
                "pass": False,
                "score": 0,
                "reason": "Image dimensions too small to be a recognizable flag"
            }
        
        # Check for presence of red, white, and blue colors
        colors = img.getcolors(maxcolors=256*256*256)
        if not colors:
            return {
                "pass": False,
                "score": 0,
                "reason": "Could not analyze image colors"
            }
        
        # Look for flag-like color patterns (red, white, blue dominance)
        has_red = has_white = has_blue = False
        for count, color in colors:
            if isinstance(color, tuple) and len(color) >= 3:
                r, g, b = color[:3]
                # Check for red-ish colors
                if r > 150 and g < 100 and b < 100:
                    has_red = True
                # Check for white-ish colors
                if r > 200 and g > 200 and b > 200:
                    has_white = True
                # Check for blue-ish colors
                if r < 100 and g < 100 and b > 150:
                    has_blue = True
        
        if has_red and has_white and has_blue:
            return {
                "pass": True,
                "score": 1,
                "reason": "Successfully generated BMP image with flag-like colors (red, white, blue)"
            }
        else:
            missing_colors = []
            if not has_red: missing_colors.append("red")
            if not has_white: missing_colors.append("white") 
            if not has_blue: missing_colors.append("blue")
            
            return {
                "pass": False,
                "score": 0.5,
                "reason": f"Generated valid BMP but missing typical flag colors: {', '.join(missing_colors)}"
            }
            
    except Exception as e:
        return {
            "pass": False,
            "score": 0,
            "reason": f"Error during evaluation: {str(e)}"
        }

def extract_c_code(response):
    """Extract C code from the LLM response, keeping main function."""
    
    # Remove language specifiers from code blocks
    response = re.sub('```[a-z]*', '```', response)
    
    # Try to extract from code blocks first
    if response.count("```") >= 2:
        code = response.split("```")[1]
        return code.strip()
    
    # If no code blocks, assume the entire response is code
    return response.strip()

def compile_and_run_c_code(code):
    """Compile and run C code, returning stdout as bytes."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        c_file = os.path.join(temp_dir, "main.c")
        exe_file = os.path.join(temp_dir, "main")
        
        try:
            # Write C code to file
            with open(c_file, 'w') as f:
                f.write(code)
            
            # Compile with gcc
            compile_result = subprocess.run(
                ["gcc", "-o", exe_file, c_file, "-lm"],
                capture_output=True,
                timeout=30
            )
            
            if compile_result.returncode != 0:
                print(f"Compilation failed: {compile_result.stderr.decode()}")
                return None
            
            # Run the executable and capture stdout as bytes
            run_result = subprocess.run(
                [exe_file],
                capture_output=True,
                timeout=30
            )
            
            if run_result.returncode != 0:
                print(f"Execution failed: {run_result.stderr.decode()}")
                return None
            
            return run_result.stdout
            
        except subprocess.TimeoutExpired:
            print("Code execution timed out")
            return None
        except Exception as e:
            print(f"Error compiling/running code: {str(e)}")
            return None