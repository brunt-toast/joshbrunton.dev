---
title: Make sure your Windows PATH is accessible in WSL
date: 2026-04-14
tags: [WSL, Linux]
---

Sometimes, by default, your Windows host machine's PATH is accessible to WSL. This means that you can call Windows executables from inside a WSL shell. 

## Ensuring the Windows PATH is available

If the Windows PATH isn't available by default, a simple shell script can make it available. 

The below script checks whether the paths have already been joined by checking for the existence of `/mnt/c/Windows` within the WSL PATH, and returning early if true. Then, it extracts the Windows PATH from `CMD.exe`, maps each entry to WSL's UNC paths using `wslpath`, and finally re-assembles the Windows PATH at the end of the Linux PATH. 

```bash
#!/bin/bash

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

## Removing the requirement for extensions

In cmd.exe, we don't have to ask for `explorer.exe` - we can just ask for `explorer`, and it works.  It decides how to resolve these based on the environment variable `PATHEXT`, which is a semicolon-separated list of file extensions, e.g. `.BAT;.EXE`. When you ask for `explorer` with this example, it will first check for `explorer.bat`, then move onto `explorer.exe`, which it finds and launches. 

In WSL, this isn't the case by default - we have to name our executable explicitly. However, we can fix that. When we fail to find a command in bash, the function `command_not_found_handle` is run, with its arguments being the command and args that were requested. Within this handler, we can query Windows' path extensions and attempt resolution on our own. 

### The Slow Way

The below function will attempt to resolve commands according to Windows' PATHEXT, mirroring Bash's default behaviour of printing "$cmd: command not found\n" and returning 127 if it still can't find it. 

```bash
__WSL_PATHEXT=$(cmd.exe /c echo %PATHEXT% 2>/dev/null | tr -d '\r')
IFS=';' read -ra __WSL_EXTS <<<"$__WSL_PATHEXT"

command_not_found_handle() {
    local cmd="$1"
    shift

    IFS=':' read -ra path_dirs <<<"$PATH"

    for dir in "${path_dirs[@]}"; do
        for ext in "${__WSL_EXTS[@]}"; do
            ext="${ext,,}"
            local candidate="$dir/$cmd$ext"
            if [[ -x "$candidate" ]]; then
                "$candidate" "$@"
                return $?
            fi
        done
    done

    printf '%s: command not found\n' "$cmd" >&2
    return 127
}

```

This script does introduce a small performance overhead. Even with its optimisations, it takes an extra 1.062s to fail to resolve a command with 11 entries in PATHEXT, vs 0.095s by default. A lot of this is because of querying the Windows filesystem from WSL, which is slow. Note that it will also attempt to run relevant binaries who come from Linux's PATH as well. 

### The Fast Way

For those who like to live fast, 1.062s is an unacceptable delay. Using caching, we can eliminate the visible overhead almost entirely.  

First, we'll need to build our cache. This can take around 10 seconds, so we don't want to do it in our shell initialisation, and definitely not in our handler. It can be run manually, but I like to keep it as a cron job at `* * * * *` (every minute), so that it remains relatively up to date. 

```bash
#!/bin/bash
set -euo pipefail

OUT_FILE="${1:-$HOME/.wsl_cmd_index.tsv}"

PATHEXT=$(cmd.exe /c echo %PATHEXT% 2>/dev/null | tr -d '\r')
IFS=';' read -ra EXTS <<<"$PATHEXT"

for i in "${!EXTS[@]}"; do
    EXTS[$i]="${EXTS[$i],,}"
done

IFS=':' read -ra PATH_DIRS <<<"$PATH"

declare -A seen=()

: > "$OUT_FILE"

for dir in "${PATH_DIRS[@]}"; do
    [[ -d "$dir" ]] || continue

    for ext in "${EXTS[@]}"; do
        for file in "$dir"/*"$ext"; do
            [[ -e "$file" ]] || continue

            base="$(basename "$file")"
            base="${base%$ext}"

            if [[ -z "${seen[$base]-}" ]]; then
                seen[$base]=1
                printf '%s\t%s\n' "$base" "$file" >> "$OUT_FILE"
            fi
        done
    done
done
```

Then, we can add the following to ~/.bashrc. This will load the index into an associative array at startup and perform an $O(1)$ lookup during resolution.  

```bash
__WSL_INDEX_FILE="$HOME/.wsl_cmd_index.tsv"

declare -A __WSL_CMD_INDEX

__wsl_load_index() {
    [[ -f "$__WSL_INDEX_FILE" ]] || return 1

    __WSL_CMD_INDEX=()

    while IFS=$'\t' read -r cmd path; do
        cmd="${cmd//$'\r'/}"
        path="${path//$'\r'/}"

        [[ -z "$cmd" || -z "$path" ]] && continue

        __WSL_CMD_INDEX["$cmd"]="$path"
    done <"$__WSL_INDEX_FILE"
}
__wsl_load_index

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