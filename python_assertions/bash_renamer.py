import subprocess
import os
import tempfile
import shutil
import re
import time

def assert_bash_renamer(response, context=None):
    # Extract code from response
    def extract_code(output):
        output = re.sub('```[a-z]*', '```', output)
        if "```" in output and output.count("```") >= 2:
            return output.split("```")[1]
        else:
            return output
    
    # Setup function
    def setup_fn():
        os.mkdir("./foo")
        time.sleep(0.5)
        
        for i in range(10):
            with open("./foo/merged_{}".format(i), "w") as f:
                f.write("a" * i)
            with open("./foo/{}".format(i), "w") as f:
                f.write("a" * i)
        
        time.sleep(0.5)
    
    # Check function
    def check_ok():
        return sorted(os.listdir("foo")) == sorted(["finished_{}".format(i) for i in range(10)] + [str(i) for i in range(10)])
    
    # Create temporary directory for test
    original_cwd = os.getcwd()
    temp_dir = tempfile.mkdtemp()
    
    try:
        os.chdir(temp_dir)
        
        # Setup test environment
        setup_fn()
        
        # Extract bash script from response
        bash_code = extract_code(response)
        
        # Write bash script to file
        with open("rename.sh", "w") as f:
            f.write(bash_code)
        
        # Make script executable
        os.chmod("rename.sh", 0o755)
        
        # Run the bash script
        result = subprocess.run(["bash", "rename.sh", "foo/"], 
                              capture_output=True, text=True, timeout=30)
        
        # Check if the renaming worked correctly
        success = check_ok()
        
        return {
            "pass": success,
            "score": 1.0 if success else 0.0,
            "reason": "Files renamed correctly" if success else f"Files not renamed correctly. Current files: {sorted(os.listdir('foo'))}"
        }
        
    except Exception as e:
        return {
            "pass": False,
            "score": 0.0,
            "reason": f"Error during execution: {str(e)}"
        }
    
    finally:
        # Cleanup
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir, ignore_errors=True)