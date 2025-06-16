import subprocess
import tempfile
import os
import re

def assert_vague_loop_format(response, context=None):
    """
    Test if the model can follow vague instructions for how to print IDs following an example.
    Expected to generate IDs like 24{month:02}_{id:03} for months 1-12 and ids 1-3.
    """
    
    def extract_code(text, keep_main=True):
        """Extract code from response, similar to ExtractCode logic"""
        # Remove language specifiers from code blocks
        text = re.sub('```[a-z]*', '```', text)
        
        if "```" in text and text.count("```") >= 2:
            # Extract code between first pair of ```
            parts = text.split("```")
            if len(parts) >= 3:
                return parts[1].strip()
        
        # If no code blocks found, return the whole text
        return text.strip()
    
    def run_python_code(code):
        """Run Python code using subprocess, similar to PythonRun logic"""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # Run the code
            result = subprocess.run(
                ['python', temp_file], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            # Clean up
            os.unlink(temp_file)
            
            if result.returncode != 0:
                return f"Error: {result.stderr}"
            
            return result.stdout
            
        except subprocess.TimeoutExpired:
            if 'temp_file' in locals():
                os.unlink(temp_file)
            return "Error: Timeout"
        except Exception as e:
            if 'temp_file' in locals():
                os.unlink(temp_file)
            return f"Error: {str(e)}"
    
    # Extract code from response
    extracted_code = extract_code(response, keep_main=True)
    
    # Run the extracted code
    output = run_python_code(extracted_code)
    
    # Check for errors
    if output.startswith("Error:"):
        return {
            "pass": False,
            "score": 0,
            "reason": f"Code execution failed: {output}"
        }
    
    # Check required substrings - must contain 2401_001 and all expected IDs
    required_strings = ["2401_001"]
    
    # Generate expected ID patterns: 24{month:02}_{id:03} for months 1-12, ids 1-3
    for month in range(1, 13):
        for id_num in range(1, 4):
            required_strings.append(f"24{month:02}_{id_num:03}")
    
    # Check if all required strings are present
    missing_strings = []
    for required in required_strings:
        if required not in output:
            missing_strings.append(required)
    
    if not missing_strings:
        return {
            "pass": True,
            "score": 1,
            "reason": "All expected ID patterns found in output"
        }
    else:
        return {
            "pass": False,
            "score": 0,
            "reason": f"Missing expected patterns: {missing_strings[:5]}{'...' if len(missing_strings) > 5 else ''}"
        }