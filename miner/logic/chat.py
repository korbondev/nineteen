import aiohttp
import traceback
from fiber.logging_utils import get_logger

from core.models import payload_models
from core import tasks_config as tcfg
from miner.config import WorkerConfig
from miner.constants import map_endpoint_with_override

logger = get_logger(__name__)


async def chat_stream(
    aiohttp_client: aiohttp.ClientSession, decrypted_payload: payload_models.ChatPayload, worker_config: WorkerConfig
):
    task_config = tcfg.get_enabled_task_config(decrypted_payload.model)
    if task_config is None:
        raise ValueError(f"Task config not found for model: {decrypted_payload.model}")
    assert task_config.orchestrator_server_config.load_model_config is not None
    #print(f"Chat task config: {task_config}")

    address = None
    address, _ = map_endpoint_with_override(address, task_config.orchestrator_server_config.task, address)
    if address is None:
        model_name = task_config.orchestrator_server_config.load_model_config["model"]
        #decrypted_payload.model = model_name
        if model_name == "unsloth/Meta-Llama-3.1-8B-Instruct":
            address = worker_config.LLAMA_3_1_8B_TEXT_WORKER_URL
        elif model_name == "hugging-quants/Meta-Llama-3.1-70B-Instruct-AWQ-INT4":
            address = worker_config.LLAMA_3_1_70B_TEXT_WORKER_URL
        else:
            raise ValueError(f"Invalid model: {decrypted_payload.model}")

    assert address is not None, f"Address for model: {decrypted_payload.model} is not set in env vars!"


    async with aiohttp_client.post(address, json=decrypted_payload.model_dump(), timeout=3) as resp:
        resp.raise_for_status()
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
