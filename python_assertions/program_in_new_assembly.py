import re
import subprocess
import tempfile
import os

def check_assembly_squares(response, context=None):
    """
    Evaluates if the assembly code generates the first 20 square numbers (1, 4, 9, ..., 400)
    in memory cells 0-19.
    """
    
    def extract_code(text):
        """Extract code from markdown code blocks or return the text as-is."""
        # Remove language specifiers from code blocks
        text = re.sub(r'```[a-z]*', '```', text)
        
        if "```" in text and text.count("```") >= 2:
            # Extract content between first pair of ```
            parts = text.split("```")
            if len(parts) >= 3:
                return parts[1].strip()
        
        # Return the whole response if no code blocks found
        return text.strip()
    
    def run_assembly_emulator(instructions):
        """Run the assembly code using a simplified emulator."""
        registers = {"R1": 0, "R2": 0, "R3": 0, "R4": 0, "R5": 0, "R6": 0, "R7": 0, "R8": 0}
        memory = [0] * 100
        instruction_pointer = 0
        instructions_list = instructions.split("\n")
        flag = False
        
        def lookup(register_or_const):
            if register_or_const.startswith('R'):
                return registers[register_or_const]
            else:
                return int(register_or_const)
        
        def find_label(label):
            for i, instruction in enumerate(instructions_list):
                if instruction.strip().startswith(label + ':'):
                    return i
            raise Exception(f"Label {label} not found")
        
        bin_op = {
            "ADD": lambda a, b: a + b,
            "SUB": lambda a, b: a - b,
            "MUL": lambda a, b: a * b,
            "DIV": lambda a, b: a // b,
            "MOD": lambda a, b: a % b,
        }
        
        cmp_op = {
            "EQ": lambda a, b: a == b,
            "NEQ": lambda a, b: a != b,
            "LT": lambda a, b: a < b,
            "LTE": lambda a, b: a <= b,
            "GT": lambda a, b: a > b,
            "GTE": lambda a, b: a >= b,
        }
        
        ctr = 0
        while instruction_pointer < len(instructions_list):
            ctr += 1
            if ctr > 1000000:
                raise Exception("Infinite loop detected")
            
            # Parse instruction (remove comments and commas)
            parts = instructions_list[instruction_pointer].split("//")[0].replace(",", "").split()
            if len(parts) == 0:
                instruction_pointer += 1
                continue
            
            instruction, args = parts[0], parts[1:]
            
            if instruction == "SET":
                registers[args[0]] = lookup(args[1])
            elif instruction in bin_op:
                registers[args[0]] = bin_op[instruction](lookup(args[1]), lookup(args[2]))
            elif instruction in cmp_op:
                flag = cmp_op[instruction](lookup(args[0]), lookup(args[1]))
            elif instruction == "INC":
                registers[args[0]] += 1
            elif instruction == "DEC":
                registers[args[0]] -= 1
            elif instruction == "JT" and flag:
                instruction_pointer = find_label(args[0])
                continue
            elif instruction == "JF" and not flag:
                instruction_pointer = find_label(args[0])
                continue
            elif instruction == "JMP":
                instruction_pointer = find_label(args[0])
                continue
            elif instruction == "LOAD":
                registers[args[0]] = memory[lookup(args[1])]
            elif instruction == "STORE":
                memory[lookup(args[1])] = registers[args[0]]
            elif instruction == "HCF":
                break
            elif instruction.endswith(':'):
                # Label, just continue
                pass
            
            instruction_pointer += 1
        
        return memory
    
    try:
        # Extract the assembly code from the response
        code = extract_code(response)
        
        # Run the emulator
        memory = run_assembly_emulator(code)
        
        # Check if first 20 memory locations contain square numbers
        expected_squares = [i*i for i in range(1, 21)]  # [1, 4, 9, 16, ..., 400]
        actual_values = memory[:20]
        
        if actual_values == expected_squares:
            return {
                "pass": True,
                "score": 1.0,
                "reason": "Assembly code correctly generated the first 20 square numbers"
            }
        else:
            return {
                "pass": False,
                "score": 0.0,
                "reason": f"Expected {expected_squares}, but got {actual_values}"
            }
            
    except Exception as e:
        return {
            "pass": False,
            "score": 0.0,
            "reason": f"Error executing assembly code: {str(e)}"
        }