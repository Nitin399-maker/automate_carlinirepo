import subprocess
import json
import os

def assert_identifies_extra_brace(response, context=None):
    try:

        response_lower = response.lower()
        
        # Look for key indicators that the student identified the extra brace
        extra_brace_indicators = [
            'extra brace',
            'extra }',
            'extra curly brace',
            'curly brace }',
            'extra bracket',
            'trailing }',
            'closing brace',
            'malformed',
            'syntax error',
            'bracket mismatch'
        ]
        
        for indicator in extra_brace_indicators:
            if indicator in response_lower:
                print("got")
                return {
                    'pass': True,
                    'score': 1.0,
                    'reason': f'Student correctly identified the extra brace issue: "{indicator}" found in response'
                }
        print("not got")
        return {
        
            'pass': False,
            'score': 0.0,
            'reason': 'Student did not identify the extra curly brace as the cause of the issue'
        }
        
    except subprocess.TimeoutExpired:
        return {
            'pass': False,
            'score': 0.0,
            'reason': 'Evaluation timed out'
        }
    except Exception as e:
        return {
            'pass': False,
            'score': 0.0,
            'reason': f'Evaluation error: {str(e)}'
        }
        
        
assert_identifies_extra_brace("""
Looking at your code and the debug output, I can see the issue:

The extra curly brace ('}') at the end of your 'negative' parameter is causing the problem. In your debug output, "Title: On Evaluating Adversarial Robustness Authors: Nicholas Carlini; Anish Athalye; Nicolas Papernot; Wieland Brendel; Jonas Rauber; Dimitris Tsipras; Ian Goodfellow; Aleksander Madry; Alexey Kurakin}" has a closing curly brace that doesn't match any opening brace in your titles list, so it's not finding this title in your dataset.

To fix this, remove the extra '}' character from the end of the negative parameter value.""")