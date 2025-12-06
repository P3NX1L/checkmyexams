from tiktoken import encoding_for_model

def count_tokens(text: str, model_name: str = "gpt-4o-mini") -> int:
    try:
        enc = encoding_for_model(model_name)
    except KeyError:
        enc = encoding_for_model("cl100k_base")
    return len(enc.encode(text))
