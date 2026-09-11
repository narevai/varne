from contextlib import AbstractContextManager, ExitStack
from pathlib import Path
from typing import cast

import vcr
from vcr.cassette import Cassette

CASSETTES = [
    Path("tests/unit/providers/jsonplaceholder/cassettes/test_client/test_fetch.yaml"),
]


class CassetteManager:
    def __init__(self, cassette_paths: list[Path]):
        self.cassette_paths: list[Path] = cassette_paths
        self.casette_stack: ExitStack = ExitStack()

    def start(self) -> None:
        for cassette_path in self.cassette_paths:
            cassette_cm = cast(
                AbstractContextManager[Cassette],
                vcr.use_cassette(
                    str(cassette_path.resolve()),
                    record_mode="none",
                ),
            )
            self.casette_stack.enter_context(cassette_cm)

    def stop(self) -> None:
        self.casette_stack.close()
