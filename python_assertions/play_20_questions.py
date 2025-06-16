import subprocess
import re

def is_done_animal(guess):
    return "llama" in guess.lower()

def take_question(guess):
    if 'Question:' in guess:
        return guess.split("Question:")[-1].strip()
    else:
        return guess.strip()

def take_one_word(guess):
    words = guess.strip().split()
    return words[0] if words else ""

def get_llm_response(prompt):
    """Simple subprocess call to get LLM response - replace with your actual LLM command"""
    try:
        # Example subprocess call - modify this to match your actual LLM setup
        result = subprocess.run(
            ['python', '-c', f'print("Yes")'],  # Replace with actual LLM command
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout.strip()
    except:
        return "No"

def assert_twenty_questions_llama(response, context=None):
    """
    Evaluates if the model can successfully play 20 questions to guess a llama.
    
    Args:
        response: The initial response from the model
        context: Optional context (unused)
        
    Returns:
        dict: Result with pass/fail and details
    """
    max_iterations = 20
    current_response = response
    
    for iteration in range(max_iterations):
        # Check if the model has already guessed correctly
        if is_done_animal(current_response):
            return {
                'pass': True,
                'score': 1.0,
                'reason': f'Successfully guessed llama in {iteration + 1} questions'
            }
        
        # Extract the question from the response
        question = take_question(current_response)
        
        # Validate question format
        if not question or not question.strip().endswith('?'):
            return {
                'pass': False,
                'score': 0.0,
                'reason': f'Invalid question format at iteration {iteration + 1}: {question}'
            }
        
        # Simulate answering the question about a llama
        llm_prompt = f"I'm playing 20 questions with someone. I'm thinking of a Llama. Here's their question: {question}.\nAnswer either 'Yes' or 'No'; do not answer anything else."
        
        # Get yes/no answer (in real implementation, this would call your LLM)
        answer = get_llm_response(llm_prompt)
        first_word = take_one_word(answer)
        
        # Continue the conversation with the answer
        conversation_prompt = f"The answer to your question '{question}' is: {first_word}. What is your next question?"
        current_response = get_llm_response(conversation_prompt)
        
        # Check if this response contains the final answer
        if is_done_animal(current_response):
            return {
                'pass': True,
                'score': 1.0,
                'reason': f'Successfully guessed llama in {iteration + 1} questions'
            }
    
    # Failed to guess within max iterations
    return {
        'pass': False,
        'score': 0.0,
        'reason': f'Failed to guess llama within {max_iterations} questions'
    }