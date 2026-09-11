#!/usr/bin/env bash
set -euo pipefail

find tests -path "*/cassettes/*" -type f -name "*.yaml" |
while read -r file; do
    yq '.' "$file" |
    jq '
      [
        .interactions[].response.body.string
        | if type == "string" then
            . as $body
            | try ($body | fromjson)
              catch (
                $body
                | split("\n")
                | .[]
                | select(length > 0)
                | fromjson
              )
          else
            .
          end
      ]
    ' > "${file%.yaml}.json"
done
