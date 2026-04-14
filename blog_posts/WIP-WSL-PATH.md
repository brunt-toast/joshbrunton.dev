---
title: Implicit file extensions while invoking Windows executables via WSL
date: 2026-04-14
tags: [WSL, Linux]
---

On Linux, most executables don't have a file extension. On Windows, cmd and powershell will sort it out using magic (that I am going to ruin shortly). It can be quite annoying, then, to have to specify the file type when trying to invoke a Windows executable from WSL. 

Usually, the Windows PATH is visible to WSL by default. If for some reason it isn't, a simple shell script can fix that. The below snippet checks if the paths have already been merged by checking for the existence of `/mnt/c/Windows` within the WSL PATH, and returning early if true to avoid redundant re-runs. Then, it extracts the Windows PATH from `CMD.exe`, maps each entry to WSL-style paths using `wslpath`, and finally re-assembles the Windows PATH at the end of the Linux PATH. This should be placed in shell RC (e.g. ~/.bashrc) before any logic that relies on Windows executables. 

```bash
[[ "$PATH" =~ "/mnt/c/Windows" ]] && return 0

windows_path=$(/mnt/c/Windows/System32/cmd.exe /C echo %PATH% 2>/dev/null)
IFS=';' read -ra windows_path_entries <<<"$windows_path"

unix_paths=()
for path in "${windows_path_entries[@]}"; do
    unix_path=$(wslpath -u "$path")
    unix_paths+=("$unix_path")
done

string_to_append=$(
    IFS=:
    echo "${unix_paths[*]}"
)

export PATH="$PATH:$string_to_append"
```

Before implementing this behaviour, we need to understand how it works in Windows. When we ask `cmd.exe` for "explorer", it will first check if there are any files named "explorer" in its PATH. Failing that, it will query the environment variable `PATHEXT`, which should contain a semicolon-separated list of file extensions, e.g.: `.BAT;.EXE`. It will iterate over these extensions, looking for a match in order of which extension appears first. First, it looks for `explorer.bat`, which doesn't exist; then, it moves on to `explorer.exe`, which is found and launched. If no candidates were found, we would instead get the classic message: "'explorer' is not recognized as an internal or external command, operable program or batch file."

As previously stated, in WSL, extensions aren't implicit by default - we have to name our executable explicitly. However, we can fix that. When we fail to find a command in bash, the function `command_not_found_handle` is run, with its arguments being the command and args that were requested. Within this handler, we can query Windows' path extensions and attempt resolution on our own. 

>[!NOTE]
> `command_not_found_handle` is specific to bash. Most shells support the command not found handle concept, but many call it something different. 

Initially, I experimented with using `command -v` to check for relevant executables, but that introduced an overhead of about 3 seconds. Checking for files manually was faster, but still added about 1.1 seconds, which caused resolution to feel sluggish. Eventually, I landed on an implementation that leverages caching to add the desired behaviour with an overhead of just 0.01s. 

First, we'll need to build our cache by walking our PATH. I chose to store it as tab-separated values in the file ~/.wsl_cmd_index.tsv. Building the cache is incredibly expensive - it can take around 10 seconds, so we don't want to do it in our shell initialisation, and definitely not in our handler. I like to run it every minute using cron, to keep it up to date.

```bash
#!/usr/bin/env bash
set -euo pipefail

OUT_FILE="${1:-$HOME/.wsl_cmd_index.tsv}"

PATHEXT=$(cmd.exe /c echo %PATHEXT% 2>/dev/null | tr -d '\r')
IFS=';' read -ra EXTS <<<"$PATHEXT"

for i in "${!EXTS[@]}"; do
    EXTS[$i]="${EXTS[$i],,}"
done

IFS=':' read -ra PATH_DIRS <<<"$PATH"

declare -A seen=()

: >"$OUT_FILE"

for dir in "${PATH_DIRS[@]}"; do
    [[ -d "$dir" ]] || continue

    for ext in "${EXTS[@]}"; do
        for file in "$dir"/*"$ext"; do
            [[ -e "$file" ]] || continue

            base="$(basename "$file")"
            base="${base%$ext}"

            if [[ -z "${seen[$base]-}" ]]; then
                seen[$base]=1
                printf '%s\t%s\n' "$base" "$file" >>"$OUT_FILE"
            fi
        done
    done
done
```

Once our index is built, we can load it and add the handler in ~/.bashrc. The below snippet will load the index at startup and perform a lookup during resolution. The lookup is super fast due to the O(1) time complexity of querying an associative array (bash-talk for a hash map). If the index isn't populated, it will inherit the default behaviour.

```bash
__WSL_INDEX_FILE="$HOME/.wsl_cmd_index.tsv"

if [ -f "$__WSL_INDEX_FILE" ]; then

    declare -A __WSL_CMD_INDEX
    __WSL_CMD_INDEX=()

    while IFS=$'\t' read -r cmd path; do
        cmd="${cmd//$'\r'/}"
        path="${path//$'\r'/}"

        [[ -z "$cmd" || -z "$path" ]] && continue

        __WSL_CMD_INDEX["$cmd"]="$path"
    done <"$__WSL_INDEX_FILE"
fi

command_not_found_handle() {

    [[ -n "${1-}" ]] || return 127

    local key="${1//$'\r'/}"
    key="${key//$'\n'/}"

    local resolved=""

    if [[ -v __WSL_CMD_INDEX["$key"] ]]; then
        resolved="${__WSL_CMD_INDEX["$key"]}"
    fi

    if [[ -n "$resolved" ]]; then
        "${resolved}" "${@:2}"
        return $?
    fi

    printf '%s: command not found\n' "$key" >&2
    return 127
}
```

In terms of user-observable overhead, this adds about 200ms to shell initialisation, and only 0.01s during the command not found handle. 