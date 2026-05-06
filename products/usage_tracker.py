class UsageTracker:
    
    def __init__(self):
        self.openai_total_tokens = 0
        self.gemini_total_tokens = 0
        self.elevenlabs_total_chars = 0
    
    def add_openai_usage(self, response):
        if hasattr(response, "usage") and hasattr(response.usage, "total_tokens"):
            self.openai_total_tokens += int(response.usage.total_tokens)
    
    def add_gemini_usage(self, response):
        usage = getattr(response, "usage_metadata", None)
        if usage:
            prompt = getattr(usage, "prompt_token_count", 0)
            completion = getattr(usage, "candidates_token_count", 0)
            self.gemini_total_tokens += int(prompt) + int(completion)
    
    def add_elevenlabs_usage(self, response_headers, text):
        # Handle lowercase/uppercase header names
        cost_header = None
        for key in response_headers.keys():
            if key.lower() == "x-character-cost":
                cost_header = key
                break
        
        if cost_header:
            self.elevenlabs_total_chars += int(response_headers[cost_header])
        else:
            self.elevenlabs_total_chars += len(text)
    
    def get_totals(self):
        return (
            self.openai_total_tokens +
            self.gemini_total_tokens +
            self.elevenlabs_total_chars
        )
