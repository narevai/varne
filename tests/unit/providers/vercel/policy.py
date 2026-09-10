from tests.policy import FieldPolicy, SanitizePolicy

vercel_policy = SanitizePolicy(
    fields=(
        FieldPolicy(
            field="projects",
            keep=("id",),
            limit=2,
        ),
        FieldPolicy(
            field="protectionBypass",
            redact_keys=True,
        ),
    )
)
