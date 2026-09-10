from dataclasses import dataclass


@dataclass(frozen=True)
class FieldPolicy:
    field: str
    keep: tuple[str, ...] = ()
    limit: int | None = None
    redact_keys: bool = False
    match_field: str | None = None
    match_value: str | None = None


@dataclass(frozen=True)
class SanitizePolicy:
    fields: tuple[FieldPolicy, ...] = ()


def get_field_policy(
    key: str | None,
    policy: SanitizePolicy,
) -> FieldPolicy | None:
    if key is None:
        return None

    return next(
        (field_policy for field_policy in policy.fields if field_policy.field == key),
        None,
    )


default_policy = SanitizePolicy()
