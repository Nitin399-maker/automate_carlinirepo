import subprocess
import json
import os

def get_assertion(response, context=None):
    """
    Evaluates if the response correctly identifies that the code calculates the first 20 primes.
    """
    # Prepare the evaluation prompt
    eval_prompt = (
        "I showed a student some code that calculates 20 primes. I then tested their "
        "understanding by asking them to explain it to me. I'm going to show you their "
        "answer, I want you to evaluate whether or not their answer says something to "
        "the effect of \"it calculates the first 20 primes\". Do not judge their "
        "reasoning, just tell me if they got it right.\n"
        f"Student Answer: \"{response}\"\n\n"
        "Think out loud then answer either \"The student passes\" or \"The student fails\"."
    )
    
    # Prepare the curl command
    curl_command = [
        "curl", "-X", "POST",
        "https://llmfoundry.straive.com/openai/v1/chat/completions",
        "-H", f"Authorization: Bearer {os.environ.get('LLMFOUNDRY_TOKEN')}:my-test-project",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": eval_prompt}]
        })
    ]
    
    try:
        # Execute the curl command
        result = subprocess.run(curl_command, capture_output=True, text=True, check=True)
        
        # Parse the response
        api_response = json.loads(result.stdout)
        eval_output = api_response["choices"][0]["message"]["content"]
        
        # Check if the evaluation contains "student passes" (case insensitive)
        passes = "student passes" in eval_output.lower()
        
        return {
            "pass": passes,
            "score": 1 if passes else 0,
            "reason": f"Evaluator output: {eval_output}"
        }
        
    except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError) as e:
        return {
            "pass": False,
            "score": 0,
            "reason": f"Error during evaluation: {str(e)}"
        }