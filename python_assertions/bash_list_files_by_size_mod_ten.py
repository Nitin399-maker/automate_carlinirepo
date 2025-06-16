import os
import subprocess
import re
import tempfile
import shutil

def test_bash_list_size(response, context=None):
    """
    Test if the model can provide the correct bash command to list files in a directory 
    and sort them by the least significant digit of their size.
    """
    
    # Create temporary directory for test
    temp_dir = tempfile.mkdtemp()
    foo_dir = os.path.join(temp_dir, "foo")
    
    try:
        # Setup: Create foo directory with files of specific sizes
        os.makedirs(foo_dir)
        sizes = [921, 714, 120, 637, 366, 662, 305, 403, 49, 158]
        
        for i, size in enumerate(sizes):
            file_path = os.path.join(foo_dir, str(i))
            with open(file_path, "w") as f:
                f.write("a" * size)
        
        # Extract bash code from response
        code = extract_bash_code(response)
        if not code:
            return {"pass": False, "score": 0, "reason": "No bash code found in response"}
        
        # Run the bash command
        try:
            result = subprocess.run(
                ["bash", "-c", f"cd {temp_dir} && {code}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return {"pass": False, "score": 0, "reason": f"Bash command failed: {result.stderr}"}
            
            output = result.stdout.strip()
            
        except subprocess.TimeoutExpired:
            return {"pass": False, "score": 0, "reason": "Command timed out"}
        except Exception as e:
            return {"pass": False, "score": 0, "reason": f"Error running command: {str(e)}"}
        
        # Fix whitespace in output
        output = " ".join(output.split())
        
        # Check if output matches expected pattern: 2.*0.*5.*7.*1.*6.*4.*3.*9.*8
        # This corresponds to files sorted by least significant digit of size:
        # File 2 (size 120, LSD=0), File 0 (size 921, LSD=1), etc.
        pattern = r"2.*0.*5.*7.*1.*6.*4.*3.*9.*8"
        
        if re.search(pattern, output):
            return {"pass": True, "score": 1, "reason": "Correct file order"}
        else:
            return {"pass": False, "score": 0, "reason": f"Incorrect order. Expected pattern: {pattern}, Got: {output}"}
    
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

def extract_bash_code(response):
    """Extract bash code from response, handling code blocks and plain text"""
    # Remove language specifiers from code blocks
    response = re.sub(r'```[a-z]*', '```', response)
    
    # If there are exactly 2 backticks, extract content between them
    if response.count("```") == 2:
        parts = response.split("```")
        if len(parts) >= 2:
            return parts[1].strip()
    
    # If no code blocks, return the response as-is
    return response.strip()