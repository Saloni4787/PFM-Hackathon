def load_prompt(path):
    if not path.endswith(".txt"):
        raise ValueError(f"Only .txt file can be loaded as prompts, got {path}")
    
    with open(path, "r") as f:
        p = f.read()
        
    return p