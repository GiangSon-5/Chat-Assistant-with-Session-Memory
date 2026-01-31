import tiktoken
import logging

logger = logging.getLogger(__name__)

class TokenCounter:
    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        # Using cl100k_base as proxy for Llama 3 tokenizer in this demo environment
        try:
            self.encoding = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self.encoding = tiktoken.get_encoding("gpt2")

    def count_tokens(self, text: str) -> int:
        if not text:
            return 0
        return len(self.encoding.encode(text))

    def count_messages(self, messages: list) -> int:
        count = 0
        for msg in messages:
            count += self.count_tokens(msg.get("content", ""))
            count += 4 # Approximate overhead per message
        return count