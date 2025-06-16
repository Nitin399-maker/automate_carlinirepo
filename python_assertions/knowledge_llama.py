def get_assert(response, context=None):
    """
    Test if the model knows the LLAMA-2 70b hidden dimension size.
    Returns True if response contains "8192" or "8,192".
    """
    if not response:
        return False
    
    # Check if response contains either "8192" or "8,192"
    contains_8192 = "8192" in response
    contains_8192_comma = "8,192" in response
    
    return contains_8192 or contains_8192_comma