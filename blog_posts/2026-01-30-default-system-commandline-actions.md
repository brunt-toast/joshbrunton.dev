---
title: How To Add A Default Action With System.CommandLine
date: 2026-01-30
tags: [.NET, CLI, tutorial]
---

System.CommandLine is a library facilitates the design of command line interfaces for .NET applications. It lets you design and architect as many commands as you need, with easy parsing and validation for options and arguments. As a fan of command line utilities, it's one of my personal favourite libraries. 

## The Problem

First, let's take a look at a minimal re-creation of a problem I was facing. I had a root command that had a required option with validations (their purpose is not important here.)  

I also added sub-commands to this root command. None of these sub-commands cared about the root command's required option, yet the validations still ran. This resulted in the sub-commands requiring valid values for options that made no sense with the requested operation and had zero bearing on the outcome. 

## The Solution 

The solution here is to move all options and execution logic from the root command to a dedicated command, and have the root command function more as a dispatcher. 

As a result, we need to manually tell this root command that when no sub-command is specified, we should route our arguments to the default command.  For reliability, we'll decide whether to use a synchronous or asynchronous action based on the type of the Action. This way, we won't encounter bugs or need to change code if the synchronicity of the default command's action changes. 

This can be done using this extension method: 

```csharp
public static void SetDefaultCommand(this RootCommand source, Command defaultCommand)
{
    source.SetAction(defaultCommand.Action is AsynchronousCommandLineAction
        ? async arg => await defaultCommand.Parse(arg.Tokens.Select(t => t.Value).ToList()).InvokeAsync()
        : arg => defaultCommand.Parse(arg.Tokens.Select(t => t.Value).ToList()).Invoke());
}
```

Or, if you prefer a more object-oriented approach, derive from a class: 

```csharp
internal abstract class RootCommandWithDefaultSubCommand : RootCommand
{
    public RootCommandWithDefaultSubCommand(Command defaultCommand, params IEnumerable<Command> subCommands)
    {
        Subcommands.Add(defaultCommand);
        foreach (var command in subCommands)
        {
            Subcommands.Add(command);
        }

        SetAction(defaultCommand.Action is AsynchronousCommandLineAction
            ? async arg => await defaultCommand.Parse(arg.Tokens.Select(t => t.Value).ToList()).InvokeAsync()
            : arg => defaultCommand.Parse(arg.Tokens.Select(t => t.Value).ToList()).Invoke());
    }
}
```

## Routing The Help Option 

After these changes, `dotnet run -- -?` will return the root (dispatcher) command's help action, not the default command's help action. If we want to change this, we can override it like so. It looks a bit hacky, but [this is the official guidance](https://learn.microsoft.com/en-us/dotnet/standard/commandline/how-to-customize-help#add-sections-to-help-output).

```csharp
public RootCommandWithDefaultSubCommand(Command defaultCommand, params IEnumerable<Command> subCommands)
{
    // ... 

    HelpOption defaultCommandHelpOption = defaultCommand.Options.First(x => x is HelpOption);

    HelpOption ourHelpOption = defaultCommand.Options.First(x => x is HelpOption);

    outHelpOption.Action = defaultCommandHelpOption.Action;
}
```

Be aware that this will make it more difficult for users to discover sub-commands of the root command. 