import ujson as json


events = [
    'data: {"id":"chat-50cbc0d925aa433887c2470ad1dca79b","object":"chat.completion.chunk","created":1728072131,"model":"unsloth/Meta-Llama-3.1-8B-Instruct","choices":[{"index":0,"delta":{"content":" did the sky go to therapy? Because it had"},"logprobs":{"content":[{"token":" did","logprob":-0.007423435337841511,"bytes":[32,100,105,100],"top_logprobs":[]},{"token":" the","logprob":-0.000018358061424805783,"bytes":[32,116,104,101],"top_logprobs":[]},{"token":" sky","logprob":-0.005994437262415886,"bytes":[32,115,107,121],"top_logprobs":[]},{"token":" go","logprob":-0.009803836233913898,"bytes":[32,103,111],"top_logprobs":[]},{"token":" to","logprob":-0.00006794698856538162,"bytes":[32,116,111],"top_logprobs":[]},{"token":" therapy","logprob":-0.012131242081522942,"bytes":[32,116,104,101,114,97,112,121],"top_logprobs":[]},{"token":"?","logprob":-0.00043764073052443564,"bytes":[63],"top_logprobs":[]},{"token":" Because","logprob":-0.187180757522583,"bytes":[32,66,101,99,97,117,115,101],"top_logprobs":[]},{"token":" it","logprob":-4.410734163684538e-6,"bytes":[32,105,116],"top_logprobs":[]},{"token":" had","logprob":-0.5695164203643799,"bytes":[32,104,97,100],"top_logprobs":[]}]},"finish_reason":null}]}'
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
        logprobs_content = choice.get("logprobs", {}).get("content", [])
        if not logprobs_content:
            continue
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