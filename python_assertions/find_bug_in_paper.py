def get_assertion(response, context=None):
    """
    Evaluates if the model correctly identified incorrect equations in a LaTeX paper.
    Expected correct answer: equations [1,3,4,5,7] are incorrect.
    """
    try:
        # Extract the list from the response
        # Look for patterns like [1,2,3] or [1, 2, 3]
        import re
        
        # Find the last occurrence of a list pattern in the response
        list_pattern = r'\[([0-9,\s]+)\]'
        matches = re.findall(list_pattern, response)
        
        if not matches:
            return {
                'pass': False,
                'score': 0,
                'reason': 'No list found in response'
            }
        
        # Take the last match (as specified in original code)
        last_match = matches[-1]
        
        # Parse the numbers from the string
        try:
            # Split by comma and convert to integers
            numbers_str = last_match.split(',')
            extracted_numbers = [int(num.strip()) for num in numbers_str if num.strip().isdigit()]
        except ValueError:
            return {
                'pass': False,
                'score': 0,
                'reason': f'Could not parse numbers from: {last_match}'
            }
        
        # Expected correct answer
        expected = [1, 3, 4, 5, 7]
        
        # Check if the extracted numbers match the expected answer
        is_correct = sorted(extracted_numbers) == sorted(expected)
        
        return {
            'pass': is_correct,
            'score': 1.0 if is_correct else 0.0,
            'reason': f'Extracted: {extracted_numbers}, Expected: {expected}' + 
                     (' ✓' if is_correct else ' ✗')
        }
        
    except Exception as e:
        return {
            'pass': False,
            'score': 0,
            'reason': f'Error processing response: {str(e)}'
        }