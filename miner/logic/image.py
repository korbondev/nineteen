import time
import ujson as json
import aiohttp
from aiohttp import ClientOSError
import asyncio
from pydantic import BaseModel
from core.log import get_logger
from miner.config import WorkerConfig
from miner.constants import map_endpoint_with_override

logger = get_logger(__name__)


async def get_image_from_server(
    body: BaseModel,
    post_endpoint: str,
    worker_config: WorkerConfig,
) -> dict | None:
    assert worker_config.IMAGE_WORKER_URL is not None, "IMAGE_WORKER_URL is not set in env vars!"
    endpoint = worker_config.IMAGE_WORKER_URL.rstrip("/") + "/" + post_endpoint

    body_dict = body.model_dump()
    endpoint, engine = map_endpoint_with_override(post_endpoint, body_dict.get("model", None), endpoint)
    body_dict["engine"] = engine

    logger.info(f"in get_image_from_server() engine: {engine} sent to {endpoint}")

    started_at = time.time()
    timeout = aiohttp.ClientTimeout(total=15)

    max_retries = 3
    for retries in range(1, max_retries + 1):

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(endpoint, json=body_dict, timeout=timeout) as response:
                    # retry on 500 error
                    if 500 <= response.status < 600:
                        logger.warning(f"Attempt {retries}: Received {response.status} error. Retrying...")
                        continue
                    response.raise_for_status()
                    
                    result = await response.json()
                    delta = time.time() - started_at
                    logger.info(f"task: {engine} completed image in {round(delta, 4)} seconds")
                    return result
                
            # retry on connection error
            except (ClientOSError, asyncio.TimeoutError) as e:
                logger.warning(f"Attempt {retries}: Connection error {e}. Retrying...")
                continue
            
            # do not retry on other errors
            except Exception as e:
                logger.error(f"Error in getting image from the server {e}")
                return None

    # Exhausted all retries
    delta = time.time() - started_at
    logger.error(f"task: {engine} retried {max_retries} times and failed in {round(delta, 4)} seconds")
    return None