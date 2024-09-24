import ujson as json
import aiohttp
from pydantic import BaseModel
from core.log import get_logger
from miner.config import WorkerConfig
from miner.constants import map_endpoint_with_override

logger = get_logger(__name__)


async def get_image_from_server(
    aiohttp_client: aiohttp.ClientSession,
    body: BaseModel,
    post_endpoint: str,
    worker_config: WorkerConfig,
    timeout: float = 20.0,
) -> dict | None:
    assert worker_config.IMAGE_WORKER_URL is not None, "IMAGE_WORKER_URL is not set in env vars!"
    endpoint = worker_config.IMAGE_WORKER_URL.rstrip("/") + "/" + post_endpoint

    body_dict = body.model_dump()
    endpoint, engine = map_endpoint_with_override(post_endpoint, body_dict.get("model", None), endpoint)
    body_dict["engine"] = engine

    try:
        logger.info(f"in get_image_from_server() engine: {engine} sending request to {endpoint}")

        client_timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp_client.post(endpoint, json=body_dict, timeout=client_timeout, raise_for_status=True) as response:
            return await response.json()

    except aiohttp.ClientResponseError as error:
        error_details = {
            "status_code": error.status,
            "request_url": str(error.request_info.url),
            "request_method": error.request_info.method,
            "request_headers": dict(error.request_info.headers),
            "request_body": body_dict,
            "response_headers": dict(error.request_info.headers),
            "response_body": error.message
        }
        logger.error(f"HTTP error when getting an image from {endpoint}. Status: {error.status}")
        logger.error(f"Error details: {json.dumps(error_details, indent=2)}")

        if error.status == 400:
            logger.error("Bad request. Check if the request payload is correct.")
        elif error.status == 401:
            logger.error("Unauthorized. Check if authentication credentials are correct.")
        elif error.status == 403:
            logger.error("Forbidden. Check if the client has necessary permissions.")
        elif error.status == 404:
            logger.error(f"Not found. Verify if the endpoint {endpoint} is correct.")
        elif error.status == 500:
            logger.error("Internal server error. The image server might be experiencing issues.")

        return None
    except aiohttp.ClientError as error:
        logger.error(f"Request error when getting an image from {endpoint}")
        logger.error(f"Error details: {str(error)}")
        logger.error(f"Error type: {type(error).__name__}")

        if isinstance(error, aiohttp.ClientConnectionError):
            logger.error(f"Failed to establish a connection to {endpoint}. Check if the server is running and accessible.")
        elif isinstance(error, aiohttp.ConnectionTimeoutError):
            logger.error(f"Request timed out after {timeout} seconds. Consider increasing the timeout or check server load.")
        elif isinstance(error, aiohttp.SocketTimeoutError):
            logger.error("Timed out while waiting for a connection from the pool. The server might be overloaded.")

        return None
    except json.JSONDecodeError as error:
        logger.error(f"Failed to decode JSON response from {endpoint}")
        logger.error(f"JSON decode error: {str(error)[:1000]}")# Log first 1000 characters of the invalid JSON
        return None
    except Exception as error:
        logger.error(f"Unexpected error occurred while getting an image from {endpoint}: {str(error)}")
        logger.exception("Stack trace:")
        return None
