import subprocess
import os
import tempfile
import shutil

def assert_git_conversation(response, context=None):
    """
    Evaluates if the model can guide a user through setting up a git repo and committing files.
    """
    # Setup temporary directory
    temp_dir = tempfile.mkdtemp()
    original_dir = os.getcwd()
    
    try:
        os.chdir(temp_dir)
        
        # Initial setup - create files a and b
        with open("a", "w") as f:
            f.write("a")
        with open("b", "w") as f:
            f.write("b")
        with open("main.py", "w") as f:
            f.write("# placeholder")
            
        # Configure git
        subprocess.run(['git', 'config', '--global', 'user.email', 'you@example.com'], 
                      capture_output=True, text=True)
        subprocess.run(['git', 'config', '--global', 'user.name', 'Your Name'], 
                      capture_output=True, text=True)
        
        # Start conversation with the initial context
        conversation_history = """You are in a repository with two files `a` and `b`. Make a new git repo and then commit them both.

On each round you should just give me just one command to type, I'll run it, and give you the exact output. I'll get started:

INPUT: `pwd`

OUTPUT: `/usr/src/app`

INPUT: `ls`

OUTPUT: `main.py a b`

Now your turn. What do you want to run? Do not explain yourself, just give me exactly one command. Start your response with INPUT:"""
        
        current_response = response
        max_iterations = 4
        
        for iteration in range(max_iterations):
            # Extract command from response
            if 'INPUT:' in current_response:
                command_part = current_response.split("INPUT:")[1]
            else:
                command_part = current_response
                
            try:
                if '`' in command_part:
                    command = command_part.split("`")[1]
                else:
                    command = command_part.split("\n")[0].strip()
            except:
                command = command_part.strip()
            
            if not command:
                break
                
            # Execute the command
            try:
                result = subprocess.run(command, shell=True, capture_output=True, 
                                      text=True, timeout=10)
                output = result.stdout.strip() if result.stdout else result.stderr.strip()
            except subprocess.TimeoutExpired:
                output = "Command timed out"
            except Exception as e:
                output = f"Error: {str(e)}"
            
            # Check if git repo is properly set up with commits
            try:
                commit_count = subprocess.run(['git', 'rev-list', '--all', '--count'], 
                                            capture_output=True, text=True)
                if commit_count.returncode == 0 and commit_count.stdout.strip() == "1":
                    return {
                        'pass': True,
                        'score': 1.0,
                        'reason': 'Successfully guided user to create git repo and commit files'
                    }
            except:
                pass
            
            # For a real conversation, we would need the next LLM response
            # Since this is a single assertion, we simulate the conversation ending
            break
        
        # Final check
        try:
            commit_count = subprocess.run(['git', 'rev-list', '--all', '--count'], 
                                        capture_output=True, text=True)
            success = (commit_count.returncode == 0 and 
                      commit_count.stdout.strip() == "1")
        except:
            success = False
        
        return {
            'pass': success,
            'score': 1.0 if success else 0.0,
            'reason': 'Git repo with one commit created' if success else 'Failed to create proper git repo'
        }
        
    finally:
        os.chdir(original_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)