import tiktoken
MILLION = 1000000
# Define model costs (verify with OpenAI's latest pricing)
MODEL_PRICING = {
    "gpt-4o": {"input": 2.5, "output": 10},  # Per 1M tokens
    "o1": {"input": 15, "output": 60},
    "o1-mini": {"input": 1.1, "output": 4.4},
    "claude-3-5-sonnet-20241022": {"input": 3, "output": 15},
    "claude-3-7-sonnet-20250219": {"input": 3, "output": 15},
    "gemini": {"input": 1.25, "output": 5},
}

def count_tokens(text, model="gpt-4o"):
    """Returns the token count for a given text and model."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")  # Default encoding
    return len(encoding.encode(text))

def compute_cost(text):
    """Computes token cost for various models."""
    print(f"Prompt text: {text[:50]}... ({len(text)} characters)\n")

    for model, pricing in MODEL_PRICING.items():
        token_count = count_tokens(text, model)
        cost = (token_count / MILLION) * pricing["input"]
        cost += (token_count * 1.5 / MILLION) * pricing["output"]
        print(f"Model: {model}")
        print(f"  - Token count: {token_count}")
        print(f"  - Cost: ${cost:.6f}\n")

def compute_cost_of_prompts(prompts, model="gpt-4o", n_outputs=1):
    total_cost = 0
    total_tokens = 0
    for prompt in prompts:
        str_prompt = ""
        for p in prompt[1]:
            str_prompt += '\n'.join([s['content'] for s in p])
        token_count = count_tokens(str_prompt, model)
        cost = (token_count / MILLION) * MODEL_PRICING[model]["input"]
        total_cost += cost
        total_tokens += token_count
        # assume 1.5x cost for output
        total_cost += (token_count * 1.3 / MILLION) * MODEL_PRICING[model]["output"] * n_outputs
    print(f"Total cost for {len(prompts)} prompts: ${total_cost:.6f}")
    print(f"Total tokens: {total_tokens}")
    return total_tokens, total_cost

if __name__ == "__main__":
    user_input = input("Enter your prompt: ")
    compute_cost(user_input)
