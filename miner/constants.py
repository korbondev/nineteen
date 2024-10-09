
TEXT_TO_IMAGE_SERVER_ENDPOINT = "text-to-image"
IMAGE_TO_IMAGE_SERVER_ENDPOINT = "image-to-image"
INPAINT_SERVER_ENDPOINT = "inpaint"
AVATAR_SERVER_ENDPOINT = "avatar"

ENDPOINT_TO_PORT_MAP = {
    # endpoint in map should have no leading / 
    "chat-llama-3-1-70b": (7405, "v1/chat/completions", None),
    "chat-llama-3-1-8b": (7105, "v1/chat/completions", None),
    "chat-llama-3-2-3b": (7205, "v1/chat/completions", None),
    "avatar": (7212, "avatar", "avatar"),
    "inpaint": (7222, "inpaint", "inpaint"),
    "proteus-text-to-image": (7231, "txt2img", "proteus"),
    "flux-schnell-text-to-image": (7251, "txt2img", "flux-schnell"),
    "dreamshaper-text-to-image": (7241, "txt2img", "dreamshaper"),
    "proteus-image-to-image": (7232, "img2img", "proteus"),
    "flux-schnell-image-to-image": (7252, "img2img", "flux-schnell"),
    "dreamshaper-image-to-image": (7242, "img2img", "dreamshaper"),
}

def map_endpoint_with_override(post_endpoint, task, default_endpoint):
    if post_endpoint in ENDPOINT_TO_PORT_MAP:
        port, endpoint, engine = ENDPOINT_TO_PORT_MAP[post_endpoint]
        return f"http://127.0.0.1:{port}/{endpoint}", engine

    if task in ENDPOINT_TO_PORT_MAP:
        port, endpoint, engine = ENDPOINT_TO_PORT_MAP[task]
        return f"http://127.0.0.1:{port}/{endpoint}", engine

    return default_endpoint, task