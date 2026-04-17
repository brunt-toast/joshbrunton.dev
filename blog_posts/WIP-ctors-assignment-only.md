If an exception is thrown in a constructor, the class being built will never be disposed or finalised. This means that any unmanaged resources that were acquired before the exception was thrown will never be cleaned up or released. 

Constructors should be for assignment and subscription only (and even then, subscription is iffy - you might prefer the messenger pattern). Since you've implemented the "set" and "add" accessors yourself in the current class, you can rest 100% assured that doing this will never throw an exception. 

```csharp
using System.Reflection;
using MethodDecorator.Fody.Interfaces;

[AttributeUsage(AttributeTargets.Class | AttributeTargets.Method)]
public class InitRequiredAttribute : Attribute, IMethodDecorator
{
    private object? _instance;
    private MethodBase? _method;

    private static readonly string[] s_excludedNames =
    [
        "Init",
        "InitAsync",
        "InitFor",
        "InitForAsync"
    ];

    public void Init(object instance, MethodBase method, object[] args)
    {
        _instance = instance;
        _method = method;
    }

    public void OnEntry()
    {
        if (_method is null
            || _method.GetCustomAttributes(typeof(InitNotRequiredAttribute), true).Length > 0
            || _method.IsConstructor
            || _method.IsSpecialName
            || s_excludedNames.Contains(_method.Name, StringComparer.InvariantCultureIgnoreCase))
        {
            return;
        }

        if (_instance is IInitializable { IsInitialized: false })
        {
            throw new InvalidOperationException("Object not initialized.");
        }
    }

    public void OnExit() { }
    public void OnException(Exception exception) { }
}

[AttributeUsage(AttributeTargets.Method)]
public class InitNotRequiredAttribute : Attribute;

```

```
[AttributeUsage(AttributeTargets.Method)]
public class InitRequiredAttribute : Attribute, IMethodDecorator
{
    private object? _instance;

    public void Init(object instance, MethodBase method, object[] args)
        => _instance = instance;

    public void OnEntry()
    {
        if (_instance is IInitializable { IsInitialized: false })
        {
            throw new InvalidOperationException("Not initialized");
        }
    }

    public void OnExit() { }
    public void OnException(Exception ex) { }
}

public interface IInitializable
{
    public bool IsInitialized { get; }
}

```
