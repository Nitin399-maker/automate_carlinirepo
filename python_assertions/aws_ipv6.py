import subprocess
import json
import os

def assert_aws_security_issue(response, context=None):
    """
    Evaluates if the response identifies overly permissive IPv6 ranges in AWS Lambda code.
    """
    
    evaluation_prompt = """Below is a software engineer's answer to a request to find an issue with the following code: {}

Does the engineer mention overly permissive IPv6 ranges? Think out loud, and then end your answer with either the string "The issue is found" or "The issue is not found"."""
    
    # Format the evaluation prompt with the response
    formatted_prompt = evaluation_prompt.format(response)
    
    # Prepare the curl command
    curl_command = [
        'curl', '-X', 'POST', 
        'https://llmfoundry.straive.com/openai/v1/chat/completions',
        '-H', f'Authorization: Bearer {os.getenv("LLMFOUNDRY_TOKEN")}:my-test-project',
        '-H', 'Content-Type: application/json',
        '-d', json.dumps({
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": formatted_prompt}]
        })
    ]
    
    # Execute the curl command
    try:
        result = subprocess.run(curl_command, capture_output=True, text=True, check=True)
        llm_response_data = json.loads(result.stdout)
        llm_evaluation = llm_response_data['choices'][0]['message']['content']
        
        success = "The issue is found" in llm_evaluation
        return {
            "pass": success,
            "score": 1.0 if success else 0.0,
            "reason": "The issue is found" if success else "The issue is not found"
        }
    
    except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError) as e:
        # If there's an error with the LLM call, fail the assertion
        return False
    
    
    
    