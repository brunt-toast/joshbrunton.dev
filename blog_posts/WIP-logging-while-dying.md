---
title: Any last words? Make sure they're logged! 
date: 2026-04-10
tags: [.NET, logging, observability, telemetry]
---

If your app is crashing, you probably want to know why. Unfortunately, that's difficult in production environments. If your app is a GUI, or running as a service, you won't get a convenient stack trace to help you track down exactly which line of code killed your app. 

If you're using a modern and optimised logging solution, there's also a decent chance that you won't know what happened leading up to the crash. This is because writing to a file is a costly operation, and to save compute, many sinks maintain an internal buffer which is flushed periodically or as a result of certain events. If your log doesn't have time to flush, you could lose up to several minutes of useful logs before a crash. 

## What you can't handle 

Some crashes just can't be handled. These include: 

* `pkill -9` (SIGKILL) for Linux or `TerminateProcess` for Windows, which kill the process at the OS level without negotiation
* Stack overflows, because we can't add new stack frames to handle them 
* Power loss or other failures coming from outside the process 
* As a result of certain code paths, like `Environment.FailFast`
* In some cases, requests to terminate while handling a request to terminate (the process may be force killed by its host)

## Common patterns

Every .NET app runs in an application domain, i.e., an execution environment. You can access the current domain of a thread using `AppDomain.CurrentDomain`, which exposes a variety of events you can subscribe to. 

>[!IMPORTANT]
> Modern .NET core apps run in a single app domain, but older versions may have multiple app domains for a single app. In this case, you may see some of these events fire multiple times. 

The `ProcessExit` event simply lets you know that your process' parent process is exiting. It gives no information about why, though it doesn't fire in the case of an unhandled exception. 

The `UnhandledException` event fires when an exception has gone unhandled up the entire call stack. Its `UnhandledExceptionEventArgs` will give you the exception that was thrown as an `object`, and indicate if the CLR is terminating. Unfortunately, it won't let you recover from the exception, since the program won't know where to resume from. 

The `FirstChanceException` event is also available, but usually overkill. It fires any time any exception is thrown anywhere, even if it's caught. The pattern is, in truth, less `try/catch/finally`, and more `try/FirstChanceException/catch/finally`. You can access the exception (typed as `Exception`), but since the handler runs before the opportunity for a catch, there's no indication of whether it will terminate the CLR. 

## Dedicated Patterns

For console apps which are terminated using <kbd>Ctrl</kbd><kbd>C</kbd> or <kbd>Ctrl</kbd><kbd>break</kbd>, you can subscribe to `Console.CancelKeyPress`. This also lets you know if it was <kbd>C</kbd> or <kbd>break</kbd> that was pressed. Note that this is not always reliable as some shells intercept these key presses and send SIGTERM instead.  

You can also subscribe to SIGTERM using `PosixSignalRegistration.Create(PosixSignal.SIGTERM, ctx => {})`. In most cases you want to respect the request and terminate the process, however it is possible to prevent termination by setting `ctx.Cancel = true`.

If you're using an `IHostApplicationLifetime`, which is recommended for modern production-scale .NET apps, you can register handlers on the cancellation tokens `ApplicationStopping` and `ApplicationStopped`. These have relatively niche uses as they provide no reason or capacity for recovery and won't fire in some error cases. 

## Summary 

Perhaps the best pattern to make sure your program's last logs are saved is: 

```csharp
AppDomain.CurrentDomain.UnhandledException += (_, e) =>
{
    _logger.Fatal(e.ExceptionObject as Exception, "Unhandled fatal exception");
    Log.CloseAndFlush();
};
AppDomain.CurrentDomain.ProcessExit += (_, _) => Log.CloseAndFlush();
```

(Example using Serilog for logging - replace with your preferred logging solution.)

This snippet works in any .NET app and guarantees that logs are flushed before your process terminates, no matter if it's graceful or not. 
