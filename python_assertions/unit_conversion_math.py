import re

def check_math_calculation(response, context=None):
    """
    Test if a model can do basic math with EE equations.
    Checks if response contains "250" followed by "hours" within 10 characters.
    """
    pattern = r"250.{,10}hours"
    match = re.search(pattern, response, re.IGNORECASE)
    
    if match:
        return {
            'pass': True,
            'score': 1.0,
            'reason': f'Found expected pattern: {match.group()}'
        }
    else:
        return {
            'pass': False,
            'score': 0.0,
            'reason': f'Expected pattern "250...hours" not found in response'
        }