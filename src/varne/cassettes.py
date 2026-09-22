from contextlib import AbstractContextManager, ExitStack
from pathlib import Path
from typing import Any, cast

import vcr
from loguru import logger
from vcr.cassette import Cassette, RecordMode
from vcr.request import Request


class CassetteManager:
    def __init__(self, cassette_paths: list[Path]):
        self.cassette_paths: list[Path] = cassette_paths
        self.casette_stack: ExitStack = ExitStack()

    def start(self) -> None:
        path_cassette_tmp = Path("/tmp/cassette_tmp.yaml")
        if path_cassette_tmp.exists():
            path_cassette_tmp.unlink()

        cassette_tmp = Cassette(
            path=str(path_cassette_tmp), record_mode=RecordMode.NONE
        )

        for cassette_current_path in self.cassette_paths:
            cassette_current = Cassette.load(path=cassette_current_path)
            logger.debug(f"Loading cassette {cassette_current_path}")

            requests = cast(list[Request], cassette_current.requests)
            responses = cast(list[dict[str, Any]], cassette_current.responses)  # pyright: ignore[reportExplicitAny]

            for request, response in zip(requests, responses, strict=True):
                cassette_tmp.append(request=request, response=response)

        cassette_tmp._save()  # pyright: ignore[reportPrivateUsage]

        cassette_cm = cast(
            AbstractContextManager[Cassette],
            vcr.use_cassette(
                path_cassette_tmp,
                record_mode="none",
                allow_playback_repeats=True,
            ),
        )

        self.casette_stack.enter_context(cassette_cm)

    def stop(self) -> None:
        self.casette_stack.close()
