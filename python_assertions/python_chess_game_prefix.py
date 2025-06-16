import subprocess
import re
import tempfile
import os

def get_assertion(response, context=None):
    """
    Evaluates Python chess prefix printing functionality.
    Returns {"pass": bool, "score": float, "reason": str}
    """
    
    def extract_code(output):
        """Extract code from LLM response, similar to ExtractCode DSL node"""
        output = re.sub('```[a-z]*', '```', output)
        if "```" in output and output.count("```") >= 2:
            # Extract code between triple backticks
            code = output.split("```")[1]
        else:
            # Use entire output if no code blocks found
            code = output
        return code.strip()
    
    def run_python_code(code, test_case):
        """Execute Python code with test case, similar to PythonRun DSL node"""
        full_code = code + "\n\n" + test_case
        
        try:
            # Write code to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(full_code)
                temp_file = f.name
            
            # Run Python code
            result = subprocess.run(
                ['python', temp_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Clean up
            os.unlink(temp_file)
            
            if result.returncode != 0:
                return f"Error: {result.stderr}"
            
            return result.stdout
            
        except subprocess.TimeoutExpired:
            if 'temp_file' in locals():
                os.unlink(temp_file)
            return "Error: Code execution timed out"
        except Exception as e:
            if 'temp_file' in locals():
                os.unlink(temp_file)
            return f"Error: {str(e)}"
    
    def check_output(txt):
        """Check if output contains expected pattern, similar to PyFunc DSL node"""
        if isinstance(txt, str):
            count = txt.count('1. Nf3 Nf6 2. c4 g6 3. Nc3 Bg7')
            return count > 10
        return False
    
    try:
        # Extract code from LLM response
        extracted_code = extract_code(response)
        
        # Define test case
        test_case = """import io
import chess.pgn
print_all_prefixes(chess.pgn.read_game(io.StringIO('1. Nf3 Nf6 2. c4 g6 3. Nc3 Bg7 4. d4 O-O 5. Bf4 d5 6. Qb3 dxc4 7. Qxc4 c6 8. e4 Nbd7 9. Rd1 Nb6 10. Qc5 Bg4 11. Bg5 Na4 12. Qa3 Nxc3 13. bxc3 Nxe4 14. Bxe7 Qb6 15. Bc4 Nxc3')))"""
        
        # Run the code
        output = run_python_code(extracted_code, test_case)
        
        # Check if output passes the test
        passes = check_output(output)
        
        if passes:
            return {
                "pass": True,
                "score": 1.0,
                "reason": "Successfully implemented print_all_prefixes function that outputs PGN notation for all game prefixes"
            }
        else:
            return {
                "pass": False,
                "score": 0.0,
                "reason": f"Function did not produce expected output pattern. Output: {output[:200]}..."
            }
    
    except Exception as e:
        return {
            "pass": False,
            "score": 0.0,
            "reason": f"Evaluation failed: {str(e)}"
        }