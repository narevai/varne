from tests.policy import FieldPolicy, SanitizePolicy

vercel_policy = SanitizePolicy(
    fields=(
        FieldPolicy(
            field="projects",
            keep=("id",),
            limit=2,
            match_field="id",
            match_value="prj_5LAip7eW0S0iDBoLNDwa9gMTye78",
        ),
        FieldPolicy(
            field="protectionBypass",
            redact_keys=True,
        ),
    )
)
