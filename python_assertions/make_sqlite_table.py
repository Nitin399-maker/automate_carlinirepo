import subprocess
import tempfile
import os
import re

def assert_sql_table_creation(response, context=None):
    """
    Evaluate if the LLM response contains valid SQL to create a table and insert Nicholas.
    """
    
    def extract_code_from_response(response_text):
        """Extract SQL code from the LLM response."""
        # First try to extract from code blocks
        response_text = re.sub('```[a-z]*', '```', response_text)
        if response_text.count("```") >= 2:
            # Extract content between first pair of backticks
            parts = response_text.split("```")
            if len(parts) >= 3:
                return parts[1].strip()
        
        # If no code blocks, use the manual extraction approach
        manual_prompt = f"I'm going to run `sqlite3 database.db < /tmp/query.sql`. Given the following answer tell me exactly what to put into `query.sql`. DO NOT MODIFY THE CODE OR WRITE NEW CODE.\n{response_text}"
        
        # For this conversion, we'll assume the response already contains the SQL
        # In a real scenario, you'd need another LLM call here, but avoiding API calls as requested
        return response_text.strip()
    
    def check_sql_execution(sql_code):
        """Execute the SQL and check if Nicholas with age 5 and research job exists."""
        try:
            # Create temporary files
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as sql_file:
                sql_file.write(sql_code)
                sql_file_path = sql_file.name
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as check_file:
                check_file.write("SELECT * FROM people;")
                check_file_path = check_file.name
            
            # Create temporary database
            with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as db_file:
                db_path = db_file.name
            
            try:
                # Execute the creation SQL
                result = subprocess.run(
                    ['sqlite3', db_path],
                    input=sql_code,
                    text=True,
                    capture_output=True,
                    timeout=30
                )
                
                if result.returncode != 0:
                    return False, f"SQL execution failed: {result.stderr}"
                
                # Query the database to check contents
                check_result = subprocess.run(
                    ['sqlite3', '-init', check_file_path, db_path, '.exit'],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if check_result.returncode != 0:
                    return False, f"Query failed: {check_result.stderr}"
                
                output = check_result.stdout
                
                # Check if Nicholas, age 5, and research-related job are in output
                has_nicholas = "Nicholas" in output
                has_age_5 = "5" in output
                has_research = "research" in output.lower()
                
                success = has_nicholas and has_age_5 and has_research
                
                return success, {
                    'output': output,
                    'has_nicholas': has_nicholas,
                    'has_age_5': has_age_5,
                    'has_research': has_research
                }
                
            finally:
                # Clean up temporary files
                for temp_path in [sql_file_path, check_file_path, db_path]:
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
                        
        except subprocess.TimeoutExpired:
            return False, "SQL execution timed out"
        except Exception as e:
            return False, f"Execution error: {str(e)}"
    
    # Extract SQL code from response
    try:
        extracted_sql = extract_code_from_response(response)
        if not extracted_sql:
            return {
                'pass': False,
                'score': 0,
                'reason': 'No SQL code found in response'
            }
        
        # Execute and evaluate the SQL
        success, details = check_sql_execution(extracted_sql)
        
        return {
            'pass': success,
            'score': 1.0 if success else 0.0,
            'reason': f'SQL evaluation result: {details}'
        }
        
    except Exception as e:
        return {
            'pass': False,
            'score': 0,
            'reason': f'Evaluation failed: {str(e)}'
        }