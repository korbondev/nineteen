import time
import aiohttp
import traceback
from fiber.logging_utils import get_logger

from core.models import payload_models
from core import tasks_config as tcfg
from core.tasks import Task
from miner.config import WorkerConfig
from miner.constants import map_endpoint_with_override

from typing import AsyncGenerator, Any

logger = get_logger(__name__)


async def chat_stream(
    decrypted_payload: payload_models.ChatPayload, worker_config: WorkerConfig
) -> AsyncGenerator[str | None, Any]:
    

    task_config = tcfg.get_enabled_task_config(decrypted_payload.model)
    if task_config is None:
        raise ValueError(f"Task config not found for model: {decrypted_payload.model}")
    assert task_config.orchestrator_server_config.load_model_config is not None
    model_name = task_config.orchestrator_server_config.load_model_config["model"]
    decrypted_payload.model = model_name # needed for vllm endpoint

    # if task_config.task == Task.chat_llama_3_1_8b:
    #     address = worker_config.LLAMA_3_1_8B_TEXT_WORKER_URL
    # elif task_config.task == Task.chat_llama_3_1_70b:
    #     address = worker_config.LLAMA_3_1_70B_TEXT_WORKER_URL
    # else:
    #     raise ValueError(f"Invalid model: {decrypted_payload.model}")    

    address, _ = map_endpoint_with_override(None, task_config.task, None)
    assert address is not None, f"Address for model: {task_config.task} is not set in env vars!"

    logger.info(f"in chat_stream() task: {task_config.task}")

    count = 0
    started_at = time.time()
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(address, json=decrypted_payload.model_dump(), timeout=timeout) as resp:
                resp.raise_for_status()

                async for chunk_enc in resp.content:
                    if chunk := chunk_enc.decode():
                        yield chunk
                        if 'data:' in chunk:
                            count += 1
        except Exception as e:
            logger.error(
                f"Error in streaming text from the server {e}"
            )
            raise

        finally:
            delta = time.time() - started_at
            logger.info(f"task: {task_config.task} streamed {count} tokens in {round(delta, 4)} seconds @ {round(count / delta, 6)} tps")
