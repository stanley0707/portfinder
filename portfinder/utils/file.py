import json
from enum import StrEnum
from pathlib import Path

import aiofiles

from portfinder.dto import (
    Result,
    ResultFileFormatEnum,
)


async def write_txt(output_path: Path, results: list[Result]):
    async with aiofiles.open(output_path.with_suffix(".txt"), "w") as f:
        for res in results:
            if res:
                await f.write(str(res))


async def write_jsonl(output_path: Path, results: list[Result]):
    async with aiofiles.open(output_path.with_suffix(".jsonl"), "w") as f:
        for res in results:
            if res:
                await f.write(json.dumps(res.to_dict()) + "\n")


async def write_json(output_path: Path, results: list[Result]):
    async with aiofiles.open(output_path.with_suffix(".json"), "w") as f:
        await f.write(json.dumps([r.to_dict() for r in results if r], indent=2))


async def save_result(
    output_path: Path,
    fformat: ResultFileFormatEnum,
    results: list[Result],
) -> None:
    match fformat:
        case ResultFileFormatEnum.TXT:
            await write_txt(output_path, results)

        case ResultFileFormatEnum.JSON:
            await write_json(output_path, results)

        case ResultFileFormatEnum.JSONL:
            await write_jsonl(output_path, results)


def resolve_input_path(path: Path, base_dir: Path = None) -> Path:
    if path.is_absolute():
        if path.exists():
            return path
        raise FileNotFoundError(f"Absolute path not found: {path}")

    base = base_dir if base_dir is not None else Path.cwd()
    full_path = (base / path).resolve()

    if full_path.exists():
        return full_path

    raise FileNotFoundError(
        f"File not found: '{user_input}'\n"
        f"Tried paths:\n"
        f"1. Absolute: {path.absolute()}\n"
        f"2. Relative to base dir: {full_path}\n"
        f"Base dir: {base}"
    )

async def read_file(
    input_file: Path,
):
    try:
        input_path = resolve_input_path(input_file, Path.cwd())
        async with aiofiles.open(input_path, "r") as f:
            async for line in f:
                yield line.strip().replace(" ", "")
    except FileNotFoundError:
        raise ValueError(f"File not found: {input_file}")
    except PermissionError:
        raise ValueError(f"Permission denied for file: {input_file}")
