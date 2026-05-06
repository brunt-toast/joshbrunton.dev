## Terminology 

* **Job**: A process that is spawned by a shell 
* **Running**: A job that is actively doing work
* **Stopped**: A job that has been paused, and may resume
* **Terminated**: A job that has been terminated, and may not resume 
* **Disowned**: A job that was spawned by a shell, but is no longer visible to it 

## Spawning a job in the foreground

Jobs are spawned in the foreground by default when a command is run. The terminal will attach to the job and detach when the job is completed or terminated. 

## Spawning a job in the background

Jobs can be put into the background immedately by using `&` at the end. For example, `updatedb &` will run `updatedb` in the background. 

You can add more commands directly after `&`, and they will run as normal. For example, `updatedb & echo "updatedb started"`. 

To run multiple commands in sequence in the background, there are two options: wrap them in `()` to create a sub-shell (so variable changes will not persist in this scope), or in `{}` to create a command group (so changes do persist). For example: 

```bash
( updatedb; echo "updatedb complete"; ) & echo "updatedb started"
```

## Listing jobs 

The `jobs` command presents a list of jobs beloning to this terminal. 

```
[1]   Running                    sleep 10
[2]-  Stopped                    sleep 100
[3]+  Stopped                    sleep 1000
```

The number in the brackets is the job ID. Once a job is assigned an ID, its ID will never change. The ID will always be the next number after the highest ID of a running or stopped job (starting at 1 for the first job). 

`+` denotes the current job, that is, the default for `fg` and `bg` to act upon. `-` is the previous job, next in line to become the current job. 

The text to the right is the invocation of the command as it appeared in the shell. 

## Stopping a foreground job

For jobs in the foreground, use <kbd>Ctrl</kbd><kbd>Z</kbd> to immediately stop the job. This will output the job to the console: 

```
[1]+   Stopped                    sleep 10
```

## Stopping a background job

To stop a background job, use `kill -STOP %i`, where `i` is the job ID (required). 

>[!IMPORTANT]
> The `%` sign specifies that the following number is a job ID, not a process ID. 

## Resuming a stopped job 

`fg %i` will bring a job to the foreground and resume it if it is stopped. If `%i` is omitted, it implies the most recently stopped job. 

To resume a stopped job in the background, use `bg %i` - again, omitting `%i` implies the most recent job. This will output the job line. 

## Monitoring background jobs 

A job in the background will report its status after completion after the next time the terminal flushes its input; use `set -b` to report immediately (`set +b` to restore behaviour).

## Terminating a job 

To terminate a foreground job, use <kbd>Ctrl</kbd><kbd>C</kbd>. This will simply stop the job. 

To terminate a background job, use `kill %i`. You can send a signal from 1-9 using `kill -n %i` if the initial `kill` doesn't work. This will the job line. 

## Disowning a job 

To disown a job, use `disown %i`. 

By default, closing the terminal will still send SIGHUP (the hang-up signal), which some programs may take as an indicator to exit; add the `-h` flag to avoid this. 

## Notes on output streams

The job lines output by `bg` and `kill` aren't sent to `/dev/stdout` or `/dev/stderr`. They go directly to the terminal and cannot be redirected.

## Breaking it all 

`set +m` disables job control. `&` syntax and `kill` still work, but <kbd>Ctrl</kbd><kbd>Z</kbd>, `fg` and `bg` all stop working.
