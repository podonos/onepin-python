"""Async client usage with the AsyncOnePinClient."""

import asyncio
import os

from onepin import AsyncOnePinClient


async def main() -> None:
    client = AsyncOnePinClient(token=os.environ["ONEPIN_API_KEY"])

    # AsyncPager is async-iterable.
    voices = await client.voices.list()
    async for voice in voices:
        print(voice)
        break  # just the first


if __name__ == "__main__":
    asyncio.run(main())
