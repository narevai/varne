#!/usr/bin/env bash
set -euo pipefail

find tests -path "*/cassettes/*" -type f -name "*.yaml" |
while read -r file; do
    yq '.' "$file" |
    jq '
      [
        .interactions[].response.body.string
        | if type == "string" then fromjson else . end
      ]
    ' > "${file%.yaml}.json"
done
