from functools import partial
from fastapi import Depends, HTTPException

from fastapi.responses import StreamingResponse
from fiber.miner.security.encryption import decrypt_general_payload
import aiohttp
from core.models import payload_models
from fastapi.routing import APIRouter
from fiber.logging_utils import get_logger

from miner.logic.chat import chat_stream
from fiber.miner.core.configuration import Config
from fiber.miner.dependencies import get_config
from miner.config import WorkerConfig
from miner.dependencies import get_worker_config

from asyncio import TimeoutError as asyncio_TimeoutError

from contextlib import aclosing as async_ensure_close_context

logger = get_logger(__name__)


async def chat_completions(
    decrypted_payload: payload_models.ChatPayload = Depends(partial(decrypt_general_payload, payload_models.ChatPayload)),
    config: Config = Depends(get_config),
    worker_config: WorkerConfig = Depends(get_worker_config),
) -> StreamingResponse:
    logger.info("in chat_completions() starting generator StreamingResponse")

    try:
        async with async_ensure_close_context(chat_stream(config.aiohttp_client, decrypted_payload, worker_config)) as async_gen:
            try:
                return StreamingResponse(async_gen, media_type="text/event-stream")
            except asyncio_TimeoutError as e:
                logger.error(f"Timeout Error in streaming text from the server: {e}. ")
                raise HTTPException(status_code=500, detail="Error in streaming text from the server") from e

    except aiohttp.ClientError as e:
        logger.error(f"aiohttp.ClientError Error in streaming text from the server: {e}. ")
        raise HTTPException(status_code=500, detail=f"Error in streaming text from the server: {e}") from e


def factory_router() -> APIRouter:
    router = APIRouter()
    router.add_api_route("/chat/completions", chat_completions, tags=["Subnet"], methods=["POST"])
    return router
