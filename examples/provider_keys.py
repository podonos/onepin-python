"""Bring-your-own provider keys (e.g. ElevenLabs).

Provider keys let the platform call third-party providers with *your* credentials.
"""

import os

from onepin import OnePinClient


def main() -> None:
    client = OnePinClient(token=os.environ["ONEPIN_API_KEY"])

    print("provider keys:", client.provider_keys.list_provider_keys())

    # Store or replace a provider key (uncomment and supply a real key):
    # client.provider_keys.put_provider_key(
    #     provider="elevenlabs",
    #     request={"key": os.environ["ELEVENLABS_API_KEY"]},
    # )


if __name__ == "__main__":
    main()
