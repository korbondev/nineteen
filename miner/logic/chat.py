import aiohttp
import traceback
from fiber.logging_utils import get_logger
from fastapi import HTTPException
from core.models import payload_models
from core import tasks_config as tcfg

# from core.tasks import Task
from miner.config import WorkerConfig
from miner.constants import map_endpoint_with_override

from typing import AsyncGenerator, Any

logger = get_logger(__name__)


async def chat_stream(
    aiohttp_client: aiohttp.ClientSession,
    decrypted_payload: payload_models.ChatPayload,
    worker_config: WorkerConfig,
    client_timeout: float = 30.0,
) -> AsyncGenerator[str, Any]:
    """
    Stream the chat interaction with the chat server.

    Args:
        aiohttp_client (aiohttp.ClientSession): The aiohttp client to use for sending the request.
        decrypted_payload (payload_models.ChatPayload): The decrypted chat payload to send to the server.
        worker_config (WorkerConfig): The configuration of the worker service.
        client_timeout (float, optional): The timeout for the client in seconds. Defaults to 5.0.

    Yields:
        str: The response as a stream of SSE messages.
    """
    # Determine the address of the chat server to send the request to
    logger.info(f"in chat_stream() decrypted_payload.model: {decrypted_payload.model}")

    task_config = tcfg.get_enabled_task_config(decrypted_payload.model)
    if task_config is None:
        raise ValueError(f"Task config not found for model: {decrypted_payload.model}")
    assert task_config.orchestrator_server_config.load_model_config is not None
    model_name = task_config.orchestrator_server_config.load_model_config["model"]
    decrypted_payload.model = model_name  # needed for vllm endpoint

    # if task_config.task == Task.chat_llama_3_1_8b:
    #     address = worker_config.LLAMA_3_1_8B_TEXT_WORKER_URL
    # elif task_config.task == Task.chat_llama_3_1_70b:
    #     address = worker_config.LLAMA_3_1_70B_TEXT_WORKER_URL
    # else:
    #     raise ValueError(f"Invalid model: {decrypted_payload.model}")

    address, _ = map_endpoint_with_override(None, task_config.task.value, None)
    assert address is not None, f"Address for model: {task_config.task.value} is not set in env vars!"

    # Send the request to the chat server
    timeout = aiohttp.ClientTimeout(total=client_timeout)
    async with aiohttp_client.post(address, json=decrypted_payload.model_dump(), raise_for_status=True, timeout=timeout) as resp:
        if resp.status != 200:
            logger.error(f"(Not200) Error in streaming text from the server: {resp.status}.")
            raise HTTPException(status_code=500, detail=f"Error in streaming text from the server. StatCode({resp.status})")

        # Yield the response as a stream of SSE messages
        chunk = True
        async for chunk_enc in resp.content:
            chunk = None
            try:
                chunk = chunk_enc.decode()
                for event in chunk.split("\n\n"):
                    if not event.strip():
                        continue
                    prefix, _, data = event.partition(":")
                    if data.strip() == "[DONE]":
                        break
                    yield f"data: {data}\n\n"
            except Exception as e:
                logger.error(f"Error in streaming text from the server: {e}. Original chunk: {chunk}\n{traceback.format_exc()}")
                raise HTTPException(status_code=500, detail="Error in streaming text from the server") from e
            chunk = None

        if chunk is not None:
            logger.error("Error in streaming text from the server: resp.content contains no chunks.")
            raise HTTPException(status_code=500, detail="Error in streaming text from the server (resp.content empty)")

    yield ""
