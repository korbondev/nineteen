import time
import ujson as json
import aiohttp
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
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(endpoint, json=body_dict, timeout=timeout) as response:
                response.raise_for_status()
                return await response.json()

        except Exception as e:
            logger.error(f"Error in getting image from the server {e}")
            return None