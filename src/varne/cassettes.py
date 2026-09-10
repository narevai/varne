from contextlib import ExitStack
from pathlib import Path

import vcr

CASSETTES = [
    Path("tests/unit/providers/jsonplaceholder/cassettes/test_client/test_fetch.yaml"),
]


class CassetteManager:
    def __init__(self, cassette_paths: list[Path]):
        self.cassette_paths = cassette_paths
        self._stack = ExitStack()

    def start(self) -> None:
        for cassette_path in self.cassette_paths:
            self._stack.enter_context(
                vcr.use_cassette(
                    str(cassette_path),
                    record_mode="none",
                )
            )

    def stop(self) -> None:
        self._stack.close()
