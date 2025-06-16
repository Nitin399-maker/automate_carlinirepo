import re
import subprocess
import tempfile
import os

def assert_assembly_square_numbers(response, context=None):
    """
    Evaluates if the LLM response contains valid assembly code that generates
    the first 20 square numbers in memory cells 0-19.
    """
    
    # Extract code from response
    def extract_code(text):
        text = re.sub('```[a-z]*', '```', text)
        if "```" in text and text.count("```") >= 2:
            return text.split("```")[1].strip()
        return text.strip()
    
    code = extract_code(response)
    if not code:
        return {
            "pass": False,
            "score": 0,
            "reason": "No code found in response"
        }
    
    # Assembly emulator implementation
    def run_assembly(instructions):
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
                memory[lookup(args[1])] = lookup(args[0])
            elif instruction == "HCF":
                break
            
            instruction_pointer += 1
        
        return memory
    
    # Run the assembly code
    try:
        memory = run_assembly(code)
        expected = [i*i for i in range(1, 21)]
        actual = memory[:20]
        
        if actual == expected:
            return {
                "pass": True,
                "score": 1,
                "reason": f"Assembly code correctly generated first 20 square numbers: {actual}"
            }
        else:
            return {
                "pass": False,
                "score": 0,
                "reason": f"Expected {expected}, but got {actual}"
            }
            
    except Exception as e:
        return {
            "pass": False,
            "score": 0,
            "reason": f"Assembly execution failed: {str(e)}"
        }