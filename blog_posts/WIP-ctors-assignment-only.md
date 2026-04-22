If an exception is thrown in a constructor, the class being built will never be disposed or finalised. This means that any unmanaged resources that were acquired before the exception was thrown will never be cleaned up or released. 

Constructors should be for assignment and subscription only (and even then, subscription is iffy - you might prefer the messenger pattern). Since you've implemented the "set" and "add" accessors yourself in the current class, you can rest 100% assured that doing this will never throw an exception. 

Any logic, then, should be done in a separate "initializer" method. If this method throws in a way that leaves the object in a corrupted state, the disposer and finalizer can still run, returning unmanaged resources to their shared pools. 

But, keeping track of initialisation state takes a lot of code and discipline. You have to remember to set the initialised flag to true on every successful init, and throw at the start of any dependent method if we're not initialised. It would be so much simplier if we could automate some of that flow. 

## Common 

Later on, we'll go over two patterns: "opt in", where methods opt into requiring initialisation, and "opt out", where whole classes opt in, and methods can opt out. 

No matter which version we use, we'll need two things: An attribute to demonstrate which methods are our initialisers, and a tracker to record which instances are initialised. 

In the tracker, we're using a conditional weak table to track initialisation state. This way, we don't risk hash collisions, and we save reclaim the relevant memory when instances are cleaned up from the heap. 

```csharp
[AttributeUsage(AttributeTargets.Method)]
public class InitMethodAttribute : Attribute, IMethodDecorator
{
    private object? _instance;

    public void Init(object instance, MethodBase method, object[] args)
        => _instance = instance;

    public void OnEntry() { }

    public void OnExit()
    {
        if (_instance is not null)
        {
            InitTracker.SetIsInitialized(_instance, true);
        }
    }

    public void OnException(Exception ex) { }
}

internal static class InitTracker
{
    private static readonly WeakReferenceHashSet<object> s_data = new();

    public static bool GetIsInitialized(object instance) =>
        s_data.Contains(instance);

    public static void SetIsInitialized(object instance, bool value)
    {
        if (value)
        {
            s_data.Add(instance);
        }
        else
        {
            s_data.Remove(instance);
        }
    }

    private class WeakReferenceHashSet<T> where T : class
    {
        private static readonly object s_dummy = new();
        private readonly ConditionalWeakTable<T, object?> _data = [];

        public void Add(T item) => _data.GetOrAdd(item, s_dummy);
        public void Remove(T item) => _data.Remove(item);
        public bool Contains(T item) => _data.TryGetValue(item, out _);
    }
}
```

## Opt In 

With the following attribute, methods can be decorated with `[InitRequired]`. Then, if they run before any `[InitMethod]`-decorated method, they'll throw an exception. Don't worry, the stack trace of the method that was annotated will be preserved.  

```csharp 
[AttributeUsage(AttributeTargets.Method)]
public class InitRequiredAttribute : Attribute, IMethodDecorator
{
    private object? _instance;

    public void Init(object instance, MethodBase method, object[] args)
    {
        _instance = instance;
    }

    public void OnEntry()
    {
        if (_instance is null || !InitTracker.GetIsInitialized(_instance))
        {
            throw new InvalidOperationException($"Object not initialized. Call a method decorated with [{nameof(InitMethodAttribute)}].");
        }
    }

    public void OnExit() { }

    public void OnException(Exception ex) { }
}
```

## Opt Out 

If most methods on a class require initialisation, it can make more sense to use the "opt out" strategy. With these attribute definitions, a class can take `[InitRequired]`, and any method that is not decorated with `[InitMethod]` or `[InitNotRequired]` will throw if the instance is uninitialised (and, just as with the opt-in method, the stack trace of the annotated method is preserved). Note that constructors, getters, and setters, are excluded here, because constructors can't require initialisation, and getters/setters should not perform logic. 

```csharp 
[AttributeUsage(AttributeTargets.Class)]
public class InitRequiredAttribute : Attribute, IMethodDecorator
{
    private object? _instance;
    private MethodBase? _method;

    public void Init(object instance, MethodBase method, object[] args)
    {
        _instance = instance;
        _method = method;
    }

    public void OnEntry()
    {
        if (_method is null
            || _method.GetCustomAttributes(typeof(InitNotRequiredAttribute), true).Length > 0
            || _method.GetCustomAttributes(typeof(InitMethodAttribute), true).Length > 0
            || _method.IsConstructor
            || _method.IsSpecialName
            || _method.IsStatic)
        {
            return;
        }

        if (_instance is null || !InitTracker.GetIsInitialized(_instance))
        {
            throw new InvalidOperationException($"Object not initialized. Call a method decorated with [{nameof(InitMethodAttribute)}].");
        }
    }

    public void OnExit() { }
    public void OnException(Exception exception) { }
}

[AttributeUsage(AttributeTargets.Method)]
public class InitNotRequiredAttribute : Attribute;
```

## Concerns 

One major concern of this approach is that we are introducing object state that is stored outside the object, which is not particularly discoverable and violates the principles of object-oriented design. While it's possible to store the initialisation state within the object, this would have trade offs, such as making the classes partial, having them inherit from a base class, or some much more complicated IL weaving. If we want to make it clearer that a class can be initialized while still preserving our relatively simple solution, we can add an auto-property via an interface, however note that since it's a default implementation, it will only be available when the instance is treated as an interfaace, and not via its concrete type. 

```csharp
public interface IInitializable
{
    bool IsInitialised => InitTracker.GetIsInitialized(this);
}
```
