import subprocess
import tempfile
import os

def assert_state_water_analysis(response, context=None):
    """
    Evaluates if the response correctly identifies states with >20k km² of water 
    in the correct order: California, Louisiana, Wisconsin, Florida, Michigan, Alaska
    """
    
    # First check if all required states are present
    required_states = ["California", "Louisiana", "Wisconsin", "Florida", "Michigan", "Alaska"]
    
    for state in required_states:
        if state not in response:
            return {
                "pass": False,
                "score": 0,
                "reason": f"Missing required state: {state}"
            }
    
    # Create evaluation prompt for LLM assessment
    evaluation_prompt = f"""This is a student answer about which states have the most water: 
<A>
{response}
</A>

The correct answer is: California, Louisiana, Wisconsin, Florida, Michigan, and Alaska (in that order).

Does the student answer exactly these states in this order? Think out loud about their answer. Then, if the student got the states in this order, answer 'The student passes' otherwise answer 'The student fails'."""

    try:
        # Create temporary file for the prompt
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write(evaluation_prompt)
            prompt_file = f.name
        
        # Call LLM via subprocess (assuming ollama or similar CLI tool)
        result = subprocess.run(
            ['ollama', 'run', 'llama2', '--prompt-file', prompt_file],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Clean up temp file
        os.unlink(prompt_file)
        
        if result.returncode != 0:
            # Fallback to simple pattern matching if LLM call fails
            response_lower = response.lower()
            
            # Check for correct order by finding positions
            positions = []
            for state in required_states:
                pos = response_lower.find(state.lower())
                if pos == -1:
                    return {
                        "pass": False,
                        "score": 0,
                        "reason": f"State {state} not found in response"
                    }
                positions.append((pos, state))
            
            # Sort by position and check if order matches expected
            positions.sort()
            actual_order = [state for _, state in positions]
            
            if actual_order == required_states:
                return {
                    "pass": True,
                    "score": 1,
                    "reason": "All states present in correct order"
                }
            else:
                return {
                    "pass": False,
                    "score": 0.5,
                    "reason": f"States present but wrong order. Expected: {required_states}, Got: {actual_order}"
                }
        
        llm_output = result.stdout.strip()
        
        # Check if LLM evaluation indicates passing
        if "student passes" in llm_output.lower():
            return {
                "pass": True,
                "score": 1,
                "reason": "LLM evaluator confirmed correct answer and order"
            }
        else:
            return {
                "pass": False,
                "score": 0,
                "reason": f"LLM evaluator indicated failure: {llm_output}"
            }
            
    except subprocess.TimeoutExpired:
        return {
            "pass": False,
            "score": 0,
            "reason": "LLM evaluation timed out"
        }
    except Exception as e:
        return {
            "pass": False,
            "score": 0,
            "reason": f"Error during evaluation: {str(e)}"
        }