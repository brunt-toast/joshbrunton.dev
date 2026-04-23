---
title: A scaleable architecture for System.CommandLine apps
date: 2026-03-19
tags: [.NET]
---

System.CommandLine is one of my favourite NuGet packages, which recently came out of pre-release and launched version 2.0.0 on 2025-11-11. It facilitates building command line interfaces by providing a framework for organising commands, arguments, and options, saving you the pain of parsing them automatically. 

A lot of tutorials for System.CommandLine end up with a somewhat messy one-file program that isn't particularly extensible or testable. In this post, we'll start architect a System.CommandLine app in a way that can scale cleanly as you add more features, using object oriented principles. 

This post is not an introduction to System.CommandLine. It's assumed that you already have a passing familiarity with commands, options, and arguments, as well as the concept of dependency injection. 

## Summary 

Fundamentally, we're moving from the scripting architecture common in examples to a more object-oriented architecture and leveraging dependency injection to reduce coupling for cleaner extensions and refactors. 

## Project Structure 

First, create a new console app (`dotnet new console`), and add the packages `System.CommandLine` and `Microsoft.Extensions.DependencyInjection` (`dotnet package add [...]`). 

Add the following folders: 
* `Arguments`
* `Commands`
* `Options`
* `Services`

## Making a service 

If we follow the single responsibility principle, we can say that the responsibility of a command is to map user input (arguments and options) to application logic. Just as the command won't know anything more than the types of its arguments and options, it shouldn't know the specific implementation of the logic they're used in. 

For this reason, we'll add services for our application logic to keep our command definitions brief and clean. 

```csharp
internal class HelloService : IHelloService 
{
    public void SayHelloTo(string name)
    {
        Console.WriteLine($"Hello, {name}!");
    }
}

internal interface IHelloService
{
    void SayHelloTo(string name);
}
```

## Defining a command 

All commands should be defined under the `Commands` folder/namespace. Instead of creating a `new Command(/*...*/)` and setting properties on it, we'll derive from `System.CommandLine.Command` (or `RootCommand` for a top-level command). Note that `Command` has no default constructor, so you'll need to give your command a name and description. We'll also add in our "hello" service from earlier, since we'll need it during execution. 

```csharp
internal class HelloCommand : RootCommand 
{
    private readonly IHelloService _helloService;

    public HelloCommand(IHelloService helloService)
    {
        _helloService = helloService;
    }
}
```

To tell the command what it's going to do, call `SetAction(actionFunc)` in the constructor. `actionFunc` can be any of the following types: 

* `Action<ParseResult>`
* `Func<ParseResult,int>`
* `Func<ParseResult,Task>`
* `Func<ParseResult,Task<int>>`
* `Func<ParseResult,CancellationToken,Task>`
* `Func<ParseResult,CancellationToken,Task<int>>`

This means that they'll also accept any method with any of the following signatures: 
* `void M(ParseResult arg)`
* `int M(ParseResult arg)`
* `Task M(ParseResult arg)`
* `Task M(ParseResult arg, CancellationToken ct)`
* `Task<int> M(ParseResult arg)`
* `Task<int> M(ParseResult arg, CancellationToken ct)`

We'll use `Task<int> M(ParseResult arg, CancellationToken ct)` - an int so we can indicate success in the standard "return 0" fashion, and a Task in case we want to go async later. So, the class should look something like this: 

```csharp
internal class HelloCommand : RootCommand 
{
    private readonly IHelloService _helloService;

    public HelloCommand(IHelloService helloService) 
    {
        _helloService = helloService;
        SetAction(Execute);
    }

    private Task<int> Execute(ParseResult arg, CancellationToken ct)
    {
        _helloService.SayHelloTo("world");
        return Task.FromResult(0);
    }
}
```

> [!NOTE]
> A command that succeeds should return 0. A command that fails might return a non-zero exit code based on the specific conditions of failure. 

## Using a command 

To use our command, we'll need to set it up in `Program.cs`. While at this point we could just use the constructor, we'll set up a DI container, which will help us with testing and not repeating ourselves later down the line. 

Commands should be short-lived and cheap to construct, so it's common to give them a transient lifetime. Remember to add its dependency, `IHelloService`, as well. 

In Program.cs: 

```csharp 
IServiceCollection sc = new ServiceCollection();
sc.AddTransient<IHelloService, HelloService>();
sc.AddTransient<HelloCommand>();
IServiceProvider sp = sc.BuildServiceCollection();

return await sp.GetRequiredService<HelloCommand>.Parse(args).InvokeAsync();
```

With that done, you can run your program. 
```bat
~/...# dotnet run 
Hello, world!

~/...# 
```

## Adding arguments and options

Let's add an argument to our command. Here, we'll add a "name", so we can say hello to a particular person. Just like with our command, we'll derive from `Argument<T>`. 

In `Arguments/NameArgument.cs`: 

```csharp
internal class NameArgument : Argument<string>
{
    public NameArgument() : base("name")
    {
    }
}
```

Remember to add it as a service in `Program.cs`:
```csharp 
sc.AddTransient<NameArgument>();
```

Then, inject it into our command like so. We'll need to call `Add(nameArgument)` to add it to the command, and assign it to a field so we can reference it later. 

```csharp
internal class HelloCommand : Command 
{
    private readonly NameArgument _nameArgument;

    public HelloCommand(NameArgument nameArgument) 
        : base("hello", "Say hello!")
    {
        _nameArgument = nameArgument;
        Add(nameArgument);
        SetAction(Execute);
    }

    /* ... */
}
```

Finally, consume it while executing by referencing the field we assigned. Here, we'll use `arg.GetRequiredValue()`, since we know for sure that there'll be a value provided (`NameArgument` would fail validation if not, due to its default arity of "exactly one"). 

```csharp
private Task<int> Execute(ParseResult arg, CancellationToken ct)
{
    string name = arg.GetRequiredValue(_nameArgument);
    Console.WriteLine($"Hello, {name}!");
    return Task.FromResult(0);
}
```

Then, running it: 

```bat
~/...# dotnet run 
Required argument missing for command. 

Usage: 
  MyApp.exe <name>

~/...# dotnet run -- Earth
Hello, Earth!
```

Options work largely the same as arguments. The option class should derive from `Option<T>` and be responsible only for its own validation, and the command class should consume it in the same way. 

## Afterthoughts 

With this architecture, you can easily track down the code responsible for a certain behaviour, and add new features with minimal conflicts. 

It also lends itself well to testing, since you can walk the symbol tree starting at the root command to discover commands, options, and arguments. 
