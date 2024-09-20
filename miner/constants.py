
TEXT_TO_IMAGE_SERVER_ENDPOINT = "text-to-image"
IMAGE_TO_IMAGE_SERVER_ENDPOINT = "image-to-image"
INPAINT_SERVER_ENDPOINT = "inpaint"
AVATAR_SERVER_ENDPOINT = "avatar"

ENDPOINT_TO_PORT_MAP = {
    # endpoint in map should have no leading / 
    "avatar": (7212, "avatar", "avatar"),
    "inpaint": (7222, "inpaint", "inpaint"),
    "proteus-text-to-image": (7231, "txt2img", "proteus"),
    "proteus-image-to-image": (7232, "img2img", "proteus"),
    "dreamshaper-text-to-image": (7241, "txt2img", "dreamshaper"),
    "dreamshaper-image-to-image": (7242, "img2img", "dreamshaper"),
    "flux-schnell-text-to-image": (7251, "txt2img", "flux-schnell"),
    "flux-schnell-image-to-image": (7252, "img2img", "flux-schnell"),
    "chat-llama-3-1-70b": (7405, "chat/completions", None), # need to check vllm endpoint route
    "chat-llama-3-1-8b": (7105, "chat/completions", None), # need to check vllm endpoint route
}

def map_endpoint_with_override(post_endpoint, task, default_endpoint):
    if post_endpoint in ENDPOINT_TO_PORT_MAP:
        port, endpoint, engine = ENDPOINT_TO_PORT_MAP[post_endpoint]
        return f"http://127.0.0.1:{port}/{endpoint}", engine

    if task in ENDPOINT_TO_PORT_MAP:
        port, endpoint, engine = ENDPOINT_TO_PORT_MAP[task]
        return f"http://127.0.0.1:{port}/{endpoint}", engine

    return default_endpoint, task