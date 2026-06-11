---
title: Creating RenderFragments from code in Razor/Blazor
date: 2026-06-11
tags: [.NET, Razor, Blazor]
---

## Problem Context

Razor is, fundamentally, a markup language. You can't "run" Razor any more than you could run HTML or Markdown, because all it does is present structure and formatting rather than executable code. Every .razor file is ultimately  to regular old .NET code. 

Every Razor component implements the interface `Microsoft.AspNetCore.Components.IComponent`, but components can't become part of the render tree directly. Instead, the compiler looks for a property with the definition `[Parameter] public Microsoft.AspNetCore.Components.RenderFragment ChildContent { get; set; }` on the outer component, and represents the inner component as a `RenderFragment`, which is a delegate taking `RenderTreeBuilder`. From a signature perspective, it can be thought of as an `Action<RenderTreeBuilder>`, or a method with signature `void M(RenderTreeBuilder)`; from a conceptual perspective, a RenderFragment is like a compiled recipe for a component. 

Sometimes, instead of Razor, we have to work with code APIs that accept a render fragment directly, for example, `IDialogService.ShowDialogAsync` (from package `Microsoft.FluentUI.AspNetCore.Components`). In these cases, we might want to build a render fragment from an existing component. 

## Basic solution

The fundamental solution to this problem is to use a render tree builder. The below example builds a render fragment based on a component type, with optional parameters. 

>[!CAUTION] 
> If `componentType` is not assignable to `IComponent`, `builder.OpenComponent` will throw an `ArgumentException`. 

```csharp
static RenderFragment CreateRenderFragment(
    Type componentType,
    IDictionary<string, object?>? parameters = null)
{
    parameters ??= new Dictionary<string, object?>();

    return builder =>
    {
        int seq = 0;
        builder.OpenComponent(seq++, componentType);

        foreach (KeyValuePair<string, object?> kvp in parameters)
        {
            builder.AddAttribute(seq++, kvp.Key, kvp.Value);
        }

        builder.CloseComponent();
    };
}
```

>[!NOTE]
> The variable `seq` will trip analyzer warning ASP0006: "Do not use non-literal sequence numbers". The sequence number helps Blazor generate a diff between two UI states so it knows exactly what it needs to update. Razor's source generators build a literal sequence number that maps to the source code line that declares the element, which is more performant; we can't do that here since we aren't working at compile time. Understanding this, we can justifiably suppress the warning with `#pragma warning disable`. 

## Adding compiler safety

If we know the type of the component we want at compile time, we can use an overload that guarantees the `IComponent` type constraint, ensuring that we'll never hit the `ArgumentException` from passing in a non-component type. This is essentially all the generic API `builder.OpenComponent<TComponent>(int)` does under the hood.

```csharp
static RenderFragment CreateRenderFragment<TComponent>(
    IDictionary<string, object?>? parameters = null)
    where TComponent : IComponent
{
    return CreateRenderFragment(typeof(TComponent), parameters);
}
```

## Capturing the rendered component 

Sometimes, we want to have a reference to our rendered component. In Razor markup, this looks like adding `@ref="_myComponent"` to the component. We can mirror this in our hand-rolled render tree builder, too. 

Probably the best way to do this is using an action which will be run when the fragment is rendered. While `ref TComponent` might look cleaner, compiler constraints prevent us from doing this (ref parameters can't be used in lambdas), and it might be read as "this method will assign to that parameter during its run", which is false. 

The implementation is as follows: 

```csharp
static RenderFragment CreateRenderFragment<TComponent>(
    IDictionary<string, object?>? parameters = null,
    Action<TComponent>? onCaptureAction = null)
    where TComponent : IComponent
{
    parameters ??= new Dictionary<string, object?>();

    return builder =>
    {
        int seq = 0;
        builder.OpenComponent<TComponent>(seq++);

        if (onCaptureAction is not null)
        {
            builder.AddComponentReferenceCapture(seq++, 
                c => onCaptureAction.Invoke((TComponent)c));
        }

        foreach (KeyValuePair<string, object?> kvp in parameters)
        {
            builder.AddAttribute(seq++, kvp.Key, kvp.Value);
        }

        builder.CloseComponent();
    };
}
```

## Auto-populating parameters from an existing component

If we want to save the trouble of mapping every parameter's name and value into a dictionary, we can instead reflect over an existing component to find them automatically. 

Note that this creates a significant performance and memory overhead from the additional instantiation of and reflection upon the component, as well as creating limitations around ahead-of-time compilation. 

```csharp
static RenderFragment CreateRenderFragment<TComponent>(TComponent component)
    where TComponent : IComponent
{
    IDictionary<string,object?> parameters = component.GetType()
        .GetProperties(BindingFlags.Public | BindingFlags.Instance)
        .Where(p => p.GetCustomAttribute<ParameterAttribute>() != null 
                    || p.GetCustomAttribute<CascadingParameterAttribute>() != null)
        .Where(p => p.CanRead)
        .Select(p => new KeyValuePair<string,object?>(p.Name, p.GetValue(component)))
        .ToDictionary();

    return CreateRenderFragment<TComponent>(parameters); 
}
```

## Full drop-in implementation 

The following can be dropped into a project using the razor SDK to enable the easy creation of render fragments with support for automatic parameter discovery and rendered component capture. 

```csharp
using System.Reflection;
using Microsoft.AspNetCore.Components;

internal static class RenderFragmentBuilder
{
    public static RenderFragment CreateRenderFragment<TComponent>(
        TComponent component,
        Action<TComponent>? onCaptureAction = null)
        where TComponent : IComponent
    {
        return CreateRenderFragment(typeof(TComponent),
            component,
            onCaptureAction is null
                ? _ => { }
                : c => onCaptureAction.Invoke((TComponent)c));
    }

    public static RenderFragment CreateRenderFragment(
        Type componentType,
        object component,
        Action<object>? onCaptureAction = null)
    {
        IDictionary<string, object?> parameters = component.GetType()
            .GetProperties(BindingFlags.Public | BindingFlags.Instance)
            .Where(p => p.GetCustomAttribute<ParameterAttribute>() != null
                        || p.GetCustomAttribute<CascadingParameterAttribute>() != null)
            .Where(p => p.CanRead)
            .Select(p => new KeyValuePair<string, object?>(p.Name, p.GetValue(component)))
            .ToDictionary();

        return CreateRenderFragment(componentType, parameters, onCaptureAction);
    }

    public static RenderFragment CreateRenderFragment<TComponent>(
        IDictionary<string, object?>? parameters = null,
        Action<TComponent>? onCaptureAction = null)
        where TComponent : IComponent
    {
        return CreateRenderFragment(typeof(TComponent),
            parameters,
            onCaptureAction is null
                ? _ => { }
                : c => onCaptureAction.Invoke((TComponent)c));
    }

    public static RenderFragment CreateRenderFragment(
        Type componentType,
        IDictionary<string, object?>? parameters = null,
        Action<object>? onCaptureAction = null)
    {
        parameters ??= new Dictionary<string, object?>();

        return builder =>
        {
            int seq = 0;
            builder.OpenComponent(seq++, componentType);

            if (onCaptureAction is not null)
            {
                builder.AddComponentReferenceCapture(seq++, onCaptureAction.Invoke);
            }

            foreach (KeyValuePair<string, object?> kvp in parameters)
            {
                builder.AddAttribute(seq++, kvp.Key, kvp.Value);
            }

            builder.CloseComponent();
        };
    }
}
```

## Addendum: Performance optimisations

In our examples, for the sake of versatility, we used optional parameters and null checks / null-coalescing assignment to minimise self-repetition. DRY code is generally considered good, because it's less to maintain.  

It's worth noting that these checks and assignments do consume clock cycles and memory, which can add up fast in hot code paths or SSR scenarios with many concurrent sessions. In such scenarios, developers may want to separate out the definitions into leaner overloads to optimise execution speed and resource consumption. 