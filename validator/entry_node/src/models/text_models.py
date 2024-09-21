llm_models = [
    {
        "id": "chat-llama-3-1-8b",
        "name": "Meta: Llama 3.1 8B Instruct",
        "created": 8192,
        "description": "Meta's latest class of model (Llama 3.1) launched with a variety of sizes & flavors. This 8B instruct-tuned version is optimized for high quality dialogue usecases, and rapid inference.\n\nIt has demonstrated strong performance compared to leading closed-source models in human evaluations.",
        "context_length": 8192,
        "architecture": {"modality": "text->text", "tokenizer": "Llama3", "instruct_type": "llama3"},
        "pricing": {"prompt": "0.000000001", "completion": "0.000000001", "image": "0", "request": "0"},
    },
    {
        "id": "chat-llama-3-1-70b",
        "name": "Meta: Llama 3.1 70B Instruct",
        "created": 8192,
        "description": "Meta's latest class of model (Llama 3.1) launched with a variety of sizes & flavors. This 70B instruct-tuned version is optimized for high quality dialogue usecases.\n\nIt has demonstrated strong performance compared to leading closed-source models in human evaluations.",
        "context_length": 8192,
        "architecture": {"modality": "text->text", "tokenizer": "Llama3", "instruct_type": "llama3"},
        "pricing": {"prompt": "0.00000001", "completion": "0.000000001", "image": "0", "request": "0"},
    },
    {
        "id": "mattshumer/reflection-70b",
        "name": "Reflection 70B",
        "created": 1725580800,
        "description": "Reflection Llama-3.1 70B is trained with a new technique called Reflection-Tuning that teaches a LLM to detect mistakes in its reasoning and correct course.\n\nThe model was trained on synthetic data.",
        "context_length": 8192,
        "architecture": {"modality": "text->text", "tokenizer": "Llama3", "instruct_type": None},
        "pricing": {"prompt": "0.000001", "completion": "0.000001", "image": "0", "request": "0"},
        "top_provider": {"context_length": 8192, "max_completion_tokens": None, "is_moderated": False},
        "per_request_limits": None,
    },
]