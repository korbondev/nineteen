"""
Some middleware to help with development work, or for extra debugging
"""

import logging
import os
import sys
import ujson as json
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp
from colorama import Back, Fore, Style, init


init(autoreset=True)
SHOW_ALL_REQUESTS = True
SHOW_ALL_RESPONSES = True


class ColoredFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": Fore.CYAN,
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.RED + Back.WHITE,
    }

    def format(self, record):
        levelname = record.levelname
        if levelname in self.COLORS:
            levelname_color = self.COLORS[levelname] + Style.BRIGHT + levelname + Style.RESET_ALL
            record.levelname = levelname_color

        message = super().format(record)

        color = self.COLORS.get(record.levelname, Fore.WHITE)
        message = message.replace("$RESET", Style.RESET_ALL)
        message = message.replace("$BOLD", Style.BRIGHT)
        message = message.replace("$COLOR", color)
        message = message.replace("$BLUE", Fore.BLUE + Style.BRIGHT)

        return message

# NOTE: Pm2 hates this (colours aren't great), why?
def get_logger(name: str):
    logger = logging.getLogger(name.split(".")[-1])
    mode: str = os.getenv("ENV", "dev").lower()
    logger.setLevel(logging.DEBUG if mode != "prod" else logging.INFO)
    logger.handlers.clear()

    format_string = (
        "$BLUE%(asctime)s.%(msecs)03d$RESET | "
        "$COLOR$BOLD%(levelname)-8s$RESET | "
        "$BLUE%(name)s$RESET:"
        "$BLUE%(funcName)s$RESET:"
        "$BLUE%(lineno)d$RESET - "
        "$COLOR$BOLD%(message)s$RESET"
    )

    colored_formatter = ColoredFormatter(format_string, datefmt="%Y-%m-%d %H:%M:%S")

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(colored_formatter)
    logger.addHandler(console_handler)

    logger.info(f"Logging mode is {logging.getLevelName(logger.getEffectiveLevel())}")
    return logger


logger = get_logger(__name__)


async def _logging_middleware(request: Request, call_next) -> Response:
    logger.debug(f"Received request: {request.method} {request.url}")
    logger.debug(f"Request headers: {request.headers}")

    try:

        body = await request.body()
        if SHOW_ALL_REQUESTS:
            logger.debug(f"Request body: {body.decode()}")

    except Exception as e:
        logger.error(f"Error reading request body: {e}")

    response = await call_next(request)
    logger.debug(f"Response status: {response.status_code}")

    if response.status_code != 200 or SHOW_ALL_RESPONSES:

        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk

        async def new_body_iterator():
            yield response_body

        response.body_iterator = new_body_iterator()
        if response.status_code != 200:
            logger.error(f"Response error content: {response_body.decode()}")
        else:
            logger.error(f"Response non-error content: {response_body.decode()}")

    return response


async def _custom_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"An error occurred: {exc}", exc_info=True)

    # Try to provide more specific error information
    if isinstance(exc, json.JSONDecodeError):
        return JSONResponse(content={"detail": "Invalid JSON in request body"}, status_code=400)
    elif isinstance(exc, ValueError):
        return JSONResponse(content={"detail": str(exc)}, status_code=400)

    return JSONResponse(content={"detail": "Internal Server Error"})


def configure_extra_logging_middleware(app: FastAPI):
    app.middleware("http")(_logging_middleware)
    app.add_exception_handler(Exception, _custom_exception_handler)
    logger.info("Development middleware and exception handler added.")
