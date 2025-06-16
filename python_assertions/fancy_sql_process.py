import sqlite3
import subprocess
import tempfile
import os
import re

def get_assertion(response, context=None):
    # Setup the database
    conn = sqlite3.connect('people.db')
    cursor = conn.cursor()
    
    # Create table
    cursor.execute('''CREATE TABLE IF NOT EXISTS people
                 (name TEXT, favorite_friend TEXT, age INT, profession TEXT)''')
    
    # Clear existing data and insert test data
    cursor.execute('DELETE FROM people')
    people_data = [
        ('Alice', 'Bob', 29, 'Engineer'),
        ('Bob', 'Alice', 32, 'Doctor'),
        ('Charlie', 'Alice', 28, 'Artist'),
        ('David', 'Eve', 35, 'Architect'),
        ('Eve', 'Frank', 26, 'Teacher'),
        ('Frank', 'Alice', 31, 'Scientist'),
        ('Grace', 'Heidi', 30, 'Nurse'),
        ('Heidi', 'Ivy', 25, 'Lawyer'),
        ('Ivy', 'Charlie', 34, 'Chef'),
        ('Judy', 'Grace', 27, 'Accountant')
    ]
    
    cursor.executemany('INSERT INTO people VALUES (?,?,?,?)', people_data)
    conn.commit()
    conn.close()
    
    try:
        # Extract code from response
        code = extract_code_from_response(response)
        
        # Create temporary file and run the code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        # Run the code and capture output
        result = subprocess.run(['python', temp_file], 
                              capture_output=True, text=True, timeout=30)
        
        # Clean up
        os.unlink(temp_file)
        
        # Check if output contains "Grace"
        output = result.stdout + result.stderr
        return {
            'pass': 'Grace' in output,
            'score': 1.0 if 'Grace' in output else 0.0,
            'reason': f"Expected 'Grace' in output, got: {output.strip()}"
        }
        
    except Exception as e:
        return {
            'pass': False,
            'score': 0.0,
            'reason': f"Error executing code: {str(e)}"
        }
    finally:
        # Clean up database
        try:
            os.remove('people.db')
        except:
            pass

def extract_code_from_response(response):
    # Remove language specifiers from code blocks
    response = re.sub(r'```[a-z]*', '```', response)
    
    # Extract code from markdown blocks
    if '```' in response and response.count('```') >= 2:
        code = response.split('```')[1]
    else:
        code = response
    
    return code.strip()