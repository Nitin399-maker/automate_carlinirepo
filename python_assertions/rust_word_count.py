import json
import subprocess
import tempfile
import os
import re

def assert_rust_word_count(response, context=None):
    # Setup: create the test file
    txt = "it was the best of times, it was the worst of times, it was the age of wisdom, it was the age of foolishness, it was the epoch of belief, it was the epoch of incredulity, it was the season of Light, it was the season of Darkness, it was the spring of hope, it was the winter of despair, we had everything before us, we had nothing before us, we were all going direct to Heaven, we were all going direct the other way"
    os.makedirs("/tmp", exist_ok=True)
    with open("/tmp/file.txt", "w") as f:
        f.write(txt)
    
    expected_answer = {'the': 11, 'it': 10, 'was': 10, 'of': 10, 'we': 4, 'times,': 2, 'age': 2, 'epoch': 2, 'season': 2, 'had': 2, 'before': 2, 'us,': 2, 'were': 2, 'all': 2, 'going': 2, 'direct': 2, 'best': 1, 'worst': 1, 'wisdom,': 1, 'foolishness,': 1, 'belief,': 1, 'incredulity,': 1, 'Light,': 1, 'Darkness,': 1, 'spring': 1, 'hope,': 1, 'winter': 1, 'despair,': 1, 'everything': 1, 'nothing': 1, 'to': 1, 'Heaven,': 1, 'other': 1, 'way': 1}
    
    # Extract code from response
    code = response
    code = re.sub('```[a-z]*', '```', code)
    if "```" in code:
        code = code.split("```")[1]
    
    # Create temporary files
    with tempfile.TemporaryDirectory() as tmpdir:
        rust_file = os.path.join(tmpdir, "main.rs")
        exe_file = os.path.join(tmpdir, "rust_word_count")
        
        # Write Rust code to file
        with open(rust_file, "w") as f:
            f.write(code)
        
        try:
            # Compile Rust code
            compile_result = subprocess.run(
                ["rustc", "-o", exe_file, rust_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if compile_result.returncode != 0:
                return {
                    "pass": False,
                    "score": 0,
                    "reason": f"Compilation failed: {compile_result.stderr}"
                }
            
            # Run the compiled program
            run_result = subprocess.run(
                [exe_file],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if run_result.returncode != 0:
                return {
                    "pass": False,
                    "score": 0,
                    "reason": f"Runtime error: {run_result.stderr}"
                }
            
            # Extract JSON from output
            output = run_result.stdout.strip()
            output = output.replace("```json", "```")
            if "```" in output:
                json_str = output.split("```")[1]
            else:
                json_str = output
            
            # Parse JSON
            try:
                result_json = json.loads(json_str)
            except json.JSONDecodeError as e:
                return {
                    "pass": False,
                    "score": 0,
                    "reason": f"Invalid JSON output: {e}"
                }
            
            # Check if result matches expected answer
            if not isinstance(result_json, dict):
                return {
                    "pass": False,
                    "score": 0,
                    "reason": "Output is not a JSON object"
                }
            
            # Check subset evaluation - all expected keys should be present with correct values
            for key, expected_value in expected_answer.items():
                if key not in result_json:
                    return {
                        "pass": False,
                        "score": 0,
                        "reason": f"Missing key '{key}' in output"
                    }
                if result_json[key] != expected_value:
                    return {
                        "pass": False,
                        "score": 0,
                        "reason": f"Incorrect value for '{key}': expected {expected_value}, got {result_json[key]}"
                    }
            
            return {
                "pass": True,
                "score": 1,
                "reason": "Rust word count program works correctly"
            }
            
        except subprocess.TimeoutExpired:
            return {
                "pass": False,
                "score": 0,
                "reason": "Program execution timed out"
            }
        except Exception as e:
            return {
                "pass": False,
                "score": 0,
                "reason": f"Unexpected error: {str(e)}"
            }