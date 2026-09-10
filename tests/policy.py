from dataclasses import dataclass

# @dataclass(frozen=True)
# class Keep:
#     fields: tuple[str, ...]


# @dataclass(frozen=True)
# class Limit:
#     count: int = 1


# @dataclass(frozen=True)
# class ObjectPolicy:
#     keep: Keep | None = None
#     limit: Limit | None = None


@dataclass(frozen=True)
class FieldPolicy:
    field: str
    keep: tuple[str, ...] = ()
    limit: int | None = None
    redact_keys: bool = False


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
