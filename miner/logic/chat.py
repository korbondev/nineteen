import time
import aiohttp
from aiohttp import ClientOSError
import asyncio
from fiber.logging_utils import get_logger

from core.models import payload_models
from core import tasks_config as tcfg
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

    address, _ = map_endpoint_with_override(None, task_config.task.value, None)
    assert address is not None, f"Address for model: {task_config.task} is not set in env vars!"

    logger.info(f"in chat_stream() task: {task_config.task}")

    started_at = time.time()
    timeout = aiohttp.ClientTimeout(total=30)
    count = 0

    max_retries = 3

    for retries in range(1, max_retries + 1):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(address, json=decrypted_payload.model_dump(), timeout=timeout) as response:
                    # retry on 500 error
                    if 500 <= response.status < 600:
                        logger.warning(f"task: {task_config.task} attempt {retries} received {response.status} error. Retrying...")
                        continue
                    response.raise_for_status()

                    async for chunk_enc in response.content:
                        if chunk := chunk_enc.decode():
                            yield chunk
                            if 'data:' in chunk:
                                count += 1

                    delta = time.time() - started_at
                    logger.info(f"task: {task_config.task} streamed {count} tokens in {round(delta, 4)} seconds @ {round(count / delta, 6)} tps")
                    return
                
            # retry on connection error
            except (ClientOSError, asyncio.TimeoutError) as e:
                logger.warning(f"task: {task_config.task} attempt {retries}: Connection error {e}. Retrying...")
                continue

            except Exception as e:
                logger.error(
                    f"task: {task_config.task} error in streaming text from the server {e}"
                )
                raise


    # Exhausted all retries
    delta = time.time() - started_at
    logger.error(f"task: {task_config.task} retried {max_retries} times and failed in {round(delta, 4)} seconds")
    raise