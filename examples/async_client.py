"""Async client usage with the AsyncOnepinClient."""

import asyncio
import os

from onepin import AsyncOnepinClient


async def main() -> None:
    client = AsyncOnepinClient(api_key=os.environ["ONEPIN_API_KEY"])

    # AsyncPager is async-iterable.
    voices = await client.voices.list()
    async for voice in voices:
        print(voice)
        break  # just the first


if __name__ == "__main__":
    asyncio.run(main())
