import re
import subprocess
import tempfile
import os
import sys

def check(response, context=None):
    # Test cases and expected answers
    code = """
    SET R1 0
    SET R2 1
loop:
    MUL R3 R2 R2
    STORE R3 R1
    INC R1
    INC R2
    SET R3 20
    EQ R1 R3
    JF loop
"""
    
    primes = """
SET R1 2
start_find_primes:
    JMP is_prime
ready_prime:
    SET R7 1
    EQ R2 R7
    JF increment
    STORE R1 R8
    INC R8
    SET R7 100
    EQ R8 R7
    JF increment
    JMP end
increment:
    INC R1
    JMP start_find_primes
is_prime:
    SET R2 1
    SET R3 2
start_loop:
    MUL R4 R3 R3
    GT R4 R1
    JT is_prime_end
    MOD R6 R1 R3
    SET R7 0
    EQ R7 R6
    JT not_prime
    INC R3
    JMP start_loop
not_prime:
    SET R2 0
is_prime_end:
    JMP ready_prime
end:
"""

    test_case = """
# Initialize memory and registers for first test
memory1 = [0] * 1000
registers1 = {"R1": 0, "R2": 0, "R3": 0, "R4": 0, "R5": 0, "R6": 0, "R7": 0, "R8": 0}

# Test squares
result1 = evaluate(\"\"\"%s\"\"\", memory1, registers1)[:10]

# Reset memory and registers for second test
memory2 = [0] * 1000
registers2 = {"R1": 0, "R2": 0, "R3": 0, "R4": 0, "R5": 0, "R6": 0, "R7": 0, "R8": 0}

# Test primes
result2 = evaluate(\"\"\"%s\"\"\", memory2, registers2)[:10]

print("Test1:", result1)
print("Test2:", result2)
""" % (code, primes)

    def extract_code(text):
        # Clean up markdown code blocks
        text = re.sub('```[a-z]*', '```', text)
        if "```" in text and text.count("```") >= 2:
            # Extract code between triple backticks
            code_match = text.split("```")[1]
            return code_match.strip()
        else:
            # If no code blocks, return the whole text
            return text.strip()

    try:
        # Extract and clean the code
        extracted_code = extract_code(response)
        
        # Create full test code
        full_code = """# -*- coding: utf-8 -*-
from typing import List, Dict

def evaluate(program: str, memory: List[int], registers: Dict[str, int]) -> List[int]:
""" + extracted_code + "\n\n" + test_case

        # Create and run the temporary file
        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', encoding='utf-8', delete=False) as f:
                temp_file = f.name
                f.write(full_code)
                f.flush()
            
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=30
            )
            
        finally:
            # Ensure file cleanup
            if temp_file and os.path.exists(temp_file):
                try:
                    os.close(os.open(temp_file, os.O_RDONLY))
                    os.unlink(temp_file)
                except:
                    pass

        if result.returncode != 0:
            return {
                'pass': False,
                'score': 0,
                'reason': f'Code execution failed: {result.stderr}'
            }
            
        output = result.stdout
        
        # Check expected answers
        expected_answers = [
            "[1, 4, 9, 16, 25, 36, 49, 64, 81, 100]",
            "[2, 3, 5, 7, 11, 13, 17, 19, 23, 29]"
        ]
        
        matches = 0
        for answer in expected_answers:
            if answer in output:
                matches += 1
        
        if matches == 2:
            return {
                'pass': True,
                'score': 1.0,
                'reason': 'Both test cases passed'
            }
        elif matches == 1:
            return {
                'pass': False,
                'score': 0.5,
                'reason': 'Only one test case passed'
            }
        else:
            return {
                'pass': False,
                'score': 0,
                'reason': f'No test cases passed. Output: {output}'
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
            'reason': f'Error running code: {str(e)}'
        }