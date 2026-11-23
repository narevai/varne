SHORT_NAME = 5


def container_label(names: tuple[str, ...]) -> str:
    """The main container in full and the next one cut short; the rest is left out."""
    main, *others = names

    if not others:
        return main

    return f"{main}, {others[0][:SHORT_NAME]}…"
