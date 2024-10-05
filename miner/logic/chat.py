import time
import aiohttp
from aiohttp import ClientOSError, ServerTimeoutError, ConnectionTimeoutError, ClientConnectorError, ClientConnectionError
from asyncio import TimeoutError
from fiber.logging_utils import get_logger

from core.models import payload_models
from core import tasks_config as tcfg
from miner.config import WorkerConfig
from miner.constants import map_endpoint_with_override

from typing import AsyncGenerator, Any
import ujson as json

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
    # elif task_config.task == Task.chat_llama_3_2_3b:
    #     address = worker_config.LLAMA_3_2_3B_TEXT_WORKER_URL
    # else:
    #     raise ValueError(f"Invalid model: {decrypted_payload.model}")    

    address, _ = map_endpoint_with_override(None, task_config.task.value, None)
    assert address is not None, f"Address for model: {task_config.task} is not set in env vars!"

    logger.info(f"in chat_stream() task: {task_config.task}")

    started_at = time.time()
    timeout = aiohttp.ClientTimeout(total=30)
    max_retries = 3
    
    for retries in range(1, max_retries + 1):
        count = 0
        first_chunk = True
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(address, json=decrypted_payload.model_dump()) as response:
                    # retry on 500 error
                    if 500 <= response.status < 600:
                        logger.warning(f"task: {task_config.task} attempt {retries} received {response.status} error. Retrying...")
                        continue
                    response.raise_for_status()

                    async for chunk_enc in response.content:
                        # fine with vllm 0.5.5
                        # if chunk := chunk_enc.decode():
                        #     yield chunk
                        #     if 'data:' in chunk:
                        #         count += 1

                        # # need this for quality score (vllm 0.6.2)
                        # if chunk := chunk_enc.decode():
                        #     received_event_chunks = chunk.split("\n\n")
                        #     for event in received_event_chunks:
                        #         if event.strip() == "":
                        #             continue
                        #         prefix, _, data = event.partition(":")
                        #         if data.strip() == "[DONE]":
                        #             break
                        #         data2 = json.loads(data)
                        #         if data2["choices"][0].get("logprobs") is None or data2["choices"][0]["logprobs"]["content"][0].get("logprob") is None:
                        #             continue
                        #         yield f"data: {data}\n\n"
                        #         count += 1
                        
                        # Very fast and compaitble with vllm 0.6.2
                        # if chunk := chunk_enc.decode():
                        #     if chunk.startswith("data: {"):
                        #         if first_chunk:
                        #             first_chunk = False
                        #             continue
                        #         yield chunk
                        #         count += 1
                        
                        # compatible with num_scheduler_steps and vllm 0.6.2
                        # no need to do this, just set --multi-step-stream-outputs if num scheduler steps > 1
                        if chunk := chunk_enc.decode():
                            received_event_chunks = chunk.split("\n\n")
                            for event in received_event_chunks:
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
                                        yield f"data: {json.dumps(updated_data_dict)}\n\n"
                                        count += 1

                    delta = time.time() - started_at
                    logger.info(f"task: {task_config.task} streamed {count} tokens in {round(delta, 4)} seconds @ {round(count / delta, 6)} tps")
                    return

            # retry on connection error
            except (ClientOSError, ServerTimeoutError, ConnectionTimeoutError, ClientConnectorError, ClientConnectionError, TimeoutError) as e:
                logger.warning(f"task: {task_config.task} attempt {retries}: Connection error {type(e).__name__}: {e}. Retrying...")
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
