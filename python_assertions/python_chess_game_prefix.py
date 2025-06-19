import subprocess
import re
import tempfile
import os
import sys

def check_response(response, context=None):
    """
    Evaluates if the model can correctly call a python API for python-chess library.
    Extracts code, runs it with test case, and checks output.
    """
    
    def extract_code(text):
        """Extract code from markdown or plain text response"""
        # Remove language specifiers from code blocks
        text = re.sub('```[a-z]*', '```', text)
        
        if text.count("```") >= 2:
            # Extract from code blocks
            parts = text.split("```")
            for i in range(1, len(parts), 2):
                yield parts[i].strip()
        else:
            # Use entire response as code
            yield text.strip()
    
    def run_python_code(code, test_case):
        """Run Python code with test case using subprocess"""
        full_code = code + "\n\n" + test_case
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(full_code)
            temp_file = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, temp_file], 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            return result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            return "", "Timeout", 1
        except Exception as e:
            return "", str(e), 1
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def check_output(output):
        """Check if output contains expected pattern"""
        return output.count('1. Nf3 Nf6 2. c4 g6 3. Nc3 Bg7') > 10
    
    # Test case from original DSL
    test_case = """
import io
import chess.pgn

# Ensure the function is defined before calling it
if 'print_all_prefixes' not in globals():
    print("Error: print_all_prefixes function is not defined")
else:
    game = chess.pgn.read_game(io.StringIO('1. Nf3 Nf6 2. c4 g6 3. Nc3 Bg7 4. d4 O-O 5. Bf4 d5 6. Qb3 dxc4 7. Qxc4 c6 8. e4 Nbd7 9. Rd1 Nb6 10. Qc5 Bg4 11. Bg5 Na4 12. Qa3 Nxc3 13. bxc3 Nxe4 14. Bxe7 Qb6 15. Bc4 Nxc3'))
    if game:
        print_all_prefixes(game)
    else:
        print("Error: Failed to read the game")
"""
    
    # Extract code from response
    for code in extract_code(response):
        if not code or len(code.strip()) < 10:
            continue
            
        # Run the code with test case
        stdout, stderr, returncode = run_python_code(code, test_case)
        
        # Check for runtime errors
        if returncode != 0:
            return {
                'pass': False,
                'score': 0.0,
                'reason': f'Code execution failed. Error: {stderr}'
            }
            
        # Apply the original check function
        if check_output(stdout):
            return {
                'pass': True,
                'score': 1.0,
                'reason': f'Code executed successfully and produced expected pattern. Output contained the required chess notation prefix pattern more than 10 times.'
            }
        else:
            return {
                'pass': False,
                'score': 0.5,
                'reason': f'Code executed without errors but did not produce the expected output pattern. Output: {stdout[:200]}...'
            }
    
    return {
        'pass': False,
        'score': 0.0,
        'reason': 'No valid code block found or all code blocks failed to execute properly.'
    }