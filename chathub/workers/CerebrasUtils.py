import os
from typing import Any, cast
from dotenv import load_dotenv

load_dotenv()


CEREBRAS_API_KEY = cast(Any, os.getenv("CEREBRAS_API_KEY"))
CEREBRAS_API_KEY1 = cast(Any, os.getenv("CEREBRAS_API_KEY1"))
CEREBRAS_API_KEY2 = cast(Any, os.getenv("CEREBRAS_API_KEY2"))


def GetCerebrasApiKey() -> str:
    return CEREBRAS_API_KEY


def GetCerebrasApiKey1() -> str:
    return CEREBRAS_API_KEY1


def GetCerebrasApiKey2() -> str:
    return CEREBRAS_API_KEY2
