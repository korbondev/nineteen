from typing import Any
from pydantic import BaseModel, Field
from core.models import utility_models
from core.models.utility_models import SCBaseModel


class CapacityResponse(SCBaseModel):
    capacities: dict[str, float]


class TextToSpeechRequest(SCBaseModel):
    params: dict[str, Any]

class CapacityPayload(SCBaseModel):
    task_configs: list[dict[str, Any]]


class ChatPayload(SCBaseModel):
    messages: list[utility_models.Message] = Field(...)
    temperature: float = Field(default=..., title="Temperature", description="Temperature for text generation.")
    seed: int = Field(default=..., title="Seed", description="Seed for text generation.")
    model: str = Field(default=..., examples=["chat-llama-3-2-3b"], title="Model")
    stream: bool = True
    logprobs: bool = True
    top_p: float = 1.0
    top_k: int = 5
    max_tokens: int = Field(500, title="Max Tokens", description="Max tokens for text generation.")

    class Config:
        use_enum_values = True


class ImageResponse(SCBaseModel):
    image_b64: str | None
    is_nsfw: bool | None
    clip_embeddings: list[float] | None
    image_hashes: utility_models.ImageHashes | None


class TextToImagePayload(SCBaseModel):
    prompt: str = Field(...)
    negative_prompt: str = Field("", title="Negative Prompt", description="Negative Prompt for text generation.")
    seed: int = Field(0, title="Seed", description="Seed for text generation.")
    steps: int = Field(10, title="Steps", description="Steps for text generation.")
    cfg_scale: float = Field(3, title="CFG Scale", description="CFG Scale for text generation.")
    width: int = Field(1024, title="Width", description="Width for text generation.")
    height: int = Field(1024, title="Height", description="Height for text generation.")
    model: str = Field(default="proteus_text_to_image", title="Model")


class ImageToImagePayload(SCBaseModel):
    prompt: str = Field(...)
    negative_prompt: str = Field("", title="Negative Prompt", description="Negative Prompt for text generation.")
    seed: int = Field(0, title="Seed", description="Seed for text generation.")
    steps: int = Field(10, title="Steps", description="Steps for text generation.")
    cfg_scale: float = Field(3, title="CFG Scale", description="CFG Scale for text generation.")
    width: int = Field(1024, title="Width", description="Width for text generation.")
    height: int = Field(1024, title="Height", description="Height for text generation.")
    image_strength: float = Field(0.5, title="Image Strength", description="Image Strength for text generation.")
    model: str = Field(default="proteus_text_to_image", title="Model")
    init_image: str = Field(...)


class InpaintPayload(SCBaseModel):
    prompt: str = Field(...)
    negative_prompt: str | None = Field(None, title="Negative Prompt", description="Negative Prompt for text generation.")
    seed: int = Field(0, title="Seed", description="Seed for text generation.")
    steps: int = Field(10, title="Steps", description="Steps for text generation.")
    cfg_scale: float = Field(3, title="CFG Scale", description="CFG Scale for text generation.")
    width: int = Field(1024, title="Width", description="Width for text generation.")
    height: int = Field(1024, title="Height", description="Height for text generation.")
    init_image: str = Field(..., title="Init Image")
    mask_image: str = Field(..., title="Mask Image")
    model: str = Field(default="inpaint", title="Model")


class AvatarPayload(SCBaseModel):
    prompt: str = Field(...)
    negative_prompt: str | None = Field(None, title="Negative Prompt", description="Negative Prompt for text generation.")
    seed: int = Field(0, title="Seed", description="Seed for text generation.")
    steps: int = Field(10, title="Steps", description="Steps for text generation.")
    width: int = Field(1024, title="Width", description="Width for text generation.")
    height: int = Field(1024, title="Height", description="Height for text generation.")
    ipadapter_strength: float = Field(
        0.5, title="Image Adapter Strength", description="Image Adapter Strength for text generation."
    )
    control_strength: float = Field(0.5, title="Control Strength", description="Control Strength for text generation.")
    init_image: str = Field(..., title="Init Image")
    model: str = Field(default="avatar", title="Model")
