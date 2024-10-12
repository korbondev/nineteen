import ujson as json


events = [
    'data: {"id":"chat-53ff16f628194fb2aa0e13cbfb62a6e4","object":"chat.completion.chunk","created":1728071871,"model":"unsloth/Meta-Llama-3.1-8B-Instruct","choices":[{"index":0,"delta":{"content":"?"},"logprobs":{"content":[{"token":"?","logprob":-0.00043764073052443564,"bytes":[63],"top_logprobs":[]}]},"finish_reason":null}]}'
]
# add more here if needed to simulate the streaming of chunks from the LLM


# simulted chat_stream()
count = 0
for event in events:
    if event.strip() == "":
        continue
    prefix, _, data = event.partition(":")
    if data.strip() == "[DONE]":
        break
    data_dict = json.loads(data)
    choices = data_dict.get("choices", [])
    for choice in choices:
        if logprobs := choice.get("logprobs", None):
            if logprobs_content := logprobs.get("content", []):
                # Yield each token in the current scheduler step with all original fields
                for token_data in logprobs_content:
                    updated_data_dict = data_dict.copy()
                    updated_data_dict["choices"] = [
                        {
                            **choice,
                            "delta": {
                                "content": token_data.get("token", "")
                            },
                            "logprobs": {
                                **choice.get("logprobs", {}),
                                "content": [token_data]
                            }
                        }
                    ]
                    print(f"data: {json.dumps(updated_data_dict)}\n\n")
                    count += 1
