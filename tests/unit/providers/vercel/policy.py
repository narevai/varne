from tests.policy import FieldPolicy, SanitizePolicy

policy_vercel_projects = SanitizePolicy(
    fields=(
        FieldPolicy(
            field="projects",
            keep=("id", "accountId"),
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

policy_vercel_billing = SanitizePolicy(
    fields=(
        FieldPolicy(
            field="projects",
            keep=("id", "accountId"),
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
