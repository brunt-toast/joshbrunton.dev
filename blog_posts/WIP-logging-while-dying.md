---
title: Any last words? Make sure they're logged! 
date: 2026-04-10
tags: [.NET, logging, observability, telemetry]
---

If your app is crashing, you probably want to know why. Unfortunately, that's difficult in production environments. If your app is a GUI, or running as a service, you won't get a convenient stack trace to help you track down exactly which line of code killed your app. 

If you're using a modern and optimised logging solution, there's also a decent chance that you won't know what happened leading up to the crash. If your log doesn't have time to flush, you could lose up to several minutes of useful logs before a crash. 

## What you can't handle 

Some crashes just can't be handled. These include: 

* `pkill -9` (SIGKILL) or `TerminateProcess`, which kill the process at the OS level without negotiation
* Stack overflows, because we can't add new stack frames to handle them 
* Power loss or other failures coming from outside the process 
* As a result of certain code paths, like `Environment.FailFast`
* In some cases, requests to terminate while handling a request to terminate (the process may be force killed)

## Framework-specific patterns

If you're using an `IHostApplicationLifetime`, which is recommended for modern production-scale .NET apps, you can register handlers on the cancellation tokens `ApplicationStopping` and `ApplicationStopped`. 

You can also subscribe to SIGTERM using `PosixSignalRegistration.Create(PosixSignal.SIGTERM, ctx => {})`. Note that Ctrl+C doesn't always send SIGTERM - if your terminal emulator doesn't have that feature, the key combination is handled by the process. 

For console apps, you can subscribe to `Console.CancelKeyPress`, which will let you know if the key pressed was Ctrl+C or Ctrl+Break, however this won't fire if the host process is terminated. 

The running of these handlers moreso indicate that termination has been requested, rather than that it is actively happening. 

## Common patterns

Every .NET app runs in an application domain, i.e., an execution environment. You can access the current domain of a thread using `AppDomain.CurrentDomain`, which exposes a variety of events you can subscribe to. 

>[!IMPORTANT]
> Modern .NET core apps run in a single app domain, but older versions may have multiple app domains for a single app. In this case, you may see some of these events fire multiple times. 

The `ProcessExit` event simply lets you know that your process' parent process is exiting. It gives no information about why, though it doesn't fire in the case of an unhandled exception. 

The `UnhandledException` event fires when an exception has gone unhandled up the entire call stack. Its `UnhandledExceptionEventArgs` will give you the exception that was thrown as an `object`, and indicate if the CLR is terminating. Unfortunately, it won't let you recover from the exception, since the program won't know where to resume from. 

The `FirstChanceException` event is also available, but usually overkill. It fires any time any exception is thrown anywhere, even if it's caught. The pattern is, in truth, less `try/catch/finally`, and more `try/FirstChanceException/catch/finally`. You can access the exception (typed as `Exception`), but since the handler runs before the opportunity for a catch, there's no indication of whether it will terminate the CLR. 

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

(Example using Serilog - replace with your preferred logging solution.)

This snippet works in any .NET app and guarantees that logs are flushed before your process terminates, no matter if it's graceful or not. 
