class Tokenizer:
    def __init__(self, vocab):
        self.vocab = vocab
        self.unk_token = "[UNK]"
    
    def tokenize(self, text):
        """Splits text into tokens and maps them to vocabulary IDs.
        
        Args:
            text (str): Input text to tokenize
            
        Returns:
            List[int]: List of token IDs
        """
        # Split text into words
        words = text.lower().split()
        
        # Convert words to token IDs
        tokens = []
        for word in words:
            token_id = self.vocab.get(word, self.vocab.get(self.unk_token, 0))
            tokens.append(token_id)
        return tokens
