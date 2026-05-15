---
title: What is the CLR type of a dynamic variable?
date: 2026-05-15
tags: [.NET]
---

Short answer: `dynamic` doesn't map to a CLR type. Under the hood it is a plain `System.Object` which is accessed via reflection using a compiler-generated mini-interpreter. 

## What is a dynamic?

`dynamic` is a C# keyword which acts like a type alias. You can assign anything to a `dynamic` variable, and you can try to access any property or method upon one. 

The main caveat is that method and property access aren't validated at compile time. You could ask for a member that doesn't exist, and you won't find out until a `RuntimeBinderException` is thrown while executing. 

Dynamic code also results in larger binaries and slower performance than statically typed code, and limits AOT compilation (because it uses reflection under the hood, which relies on the .NET runtime). 

## What are the use cases for dynamic? 

`dynamic` is a relatively niche keyword, because the primary use case for `dynamic` is when inter-operating with external code from weakly typed languages or other situations where a call might return data of an unpredictable shape. 

Beyond that, it should be used with great care. To use `dynamic` when a type is actually known is akin to using the `any` type in TypeScript to dodge API constraints: you're throwing away the guarantees of the compiler for no good reason, sacrificing safety and often performance. 

If your solution is fully self-contained in .NET code and you're using `dynamic`, you've probably architected in a way that could be cleaner. Whenever viable, consider instead: 

* Creating method overloads to accept multiple known types as parameters 
* Returning a tuple or union to return one of multiple known types 
* Using inheritance to create logical links between classes with common properties and purposes 

## How do we know that compiled code is dynamic? 

While `dynamic` variables are essentially `objects`, built assemblies' public APIs still need to be able to reconstruct the information that a symbol is of a dynamic type so consumers can treat it as such. This is done with an attribute, `System.Runtime.CompilerServices.DynamicAttribute`. It is reserved for compiler usage, meaning that it is a compiler error for user code to annotate any symbol with it. 

Consider the lowering of the following method signature with a dynamic parameter:

```csharp
/* source  */ void M(dynamic dyn);
/* lowered */ void M([Dynamic] object dyn);
```

Or, for a dynamic return type, we annotate the entire method with a return attribute: 

```csharp
// source
dynamic M();

// lowered
[return: Dynamic]
object M();
```

If we use any generic type parameters, we pass `bool[] transformFlags` to the constructor to indicate which parameters were dynamic. The order they appear in `transformFlags` is the same order in which they are read, for example: 

```csharp
/* source  */ void M(Dictionary<object,dynamic> dyn);
/* lowered */ void M([Dynamic([false, false, true])] Dictionary<object,object> dyn)
```

(The default constructor for `DynamicAttribute` sets `transformFlags` to `new bool[1] { true }`.)

The annotation doesn't appear on local variables because they aren't exposed as part of a public API. There's no way for a consumer to know about the existence of a local variable, let alone its type. (Also, because attributes aren't valid on local variables). 

## How are dynamic variables accessed?

Even in simple use cases, `dynamic` causes a lot of code to be generated around it. Shown below is an example of lowered dynamic code. 

The source code: 

```csharp
string[] arr = ["hello", "world"];
dynamic dyn = arr;
int len = dyn.Length;
```

The lowered code (with names adjusted for clarity, and compiler noise removed): 

```csharp
static class CallSites
{
    public static CallSite<Func<CallSite, object, object>> GetLengthAsObject;
    public static CallSite<Func<CallSite, object, int>> ConvertLengthObjectToInt;
}

string[] arr = ["hello", "world"];
object dyn = arr;

if (CallSites.ConvertLengthObjectToInt == null)
{
    CallSites.ConvertLengthObjectToInt = CallSite<Func<CallSite, object, int>>.Create(Microsoft.CSharp.RuntimeBinder.Binder.Convert(CSharpBinderFlags.None, typeof(int), typeof(Program)));
}

if (CallSites.GetLengthAsObject == null)
{
    CallSites.GetLengthAsObject = CallSite<Func<CallSite, object, object>>.Create(
        Microsoft.CSharp.RuntimeBinder.Binder.GetMember(
            CSharpBinderFlags.None, 
            "Length", 
            typeof(Program), 
            [CSharpArgumentInfo.Create(CSharpArgumentInfoFlags.None, null)]
        )
    );
}

object lenObj = CallSites.GetLengthAsObject.Target(CallSites.GetLengthAsObject, dyn);
int len = CallSites.ConvertLengthObjectToInt.Target(CallSites.ConvertLengthObjectToInt, lenObj);
```

Let's break down what happens here. 

First, the compiler generates a class to register all the places we'll make use of our dynamic variable, called the "call sites". To save on startup time, nothing is initialised up front. 

```csharp
static class CallSites
{
    public static CallSite<Func<CallSite, object, object>> GetLengthAsObject;
    public static CallSite<Func<CallSite, object, int>> ConvertLengthObjectToInt;
}
```

When we assign to a dynamic variable, we really just assign to an object. Every type in C# derives from object, so this cast is always safe. 

```csharp
string[] arr = ["hello", "world"];
object dyn = arr;
```

When we want to execute dynamic code, we need to define what our call sites are going to do. The statement `int len = dynamic.Length` can be expressed in two stages: Locate the object known as `arr.Length`, then convert it to an `int`. The below code builds that logic using reflection and stores it in our `CallSites` class for later re-use. 

```csharp 
if (CallSites.GetLengthAsObject == null)
{
    CallSites.GetLengthAsObject = CallSite<Func<CallSite, object, object>>.Create(
        Microsoft.CSharp.RuntimeBinder.Binder.GetMember(
            CSharpBinderFlags.None, 
            "Length", 
            typeof(Program), 
            [CSharpArgumentInfo.Create(CSharpArgumentInfoFlags.None, null)]
        )
    );
}

if (CallSites.ConvertLengthObjectToInt == null)
{
    CallSites.ConvertLengthObjectToInt = CallSite<Func<CallSite, object, int>>.Create(Microsoft.CSharp.RuntimeBinder.Binder.Convert(CSharpBinderFlags.None, typeof(int), typeof(Program)));
}
```

With our call sites constructed, we try to access the `object lenObj`.  

```csharp
object lenObj = CallSites.GetLengthAsObject.Target(CallSites.GetLengthAsObject, dyn);
```

Then, we try to convert that object into an `int len`. 

```csharp
int len = CallSites.ConvertLengthObjectToInt.Target(CallSites.ConvertLengthObjectToInt, lenObj);
```

Since the variable is dynamic, we can't know if the `Length` property will exist or if it will be of type `int`. The targets will throw `RuntimeBinderException` if they cannot execute for reasons that would usually be caught by the compiler. 

Of course, the generated code will vary wildly depending on how the dynamic is assigned and consumed, but consistent among all applications is that the compiler will treat the dynamic as an object and construct mini-interpreters *ad hoc* to try to execute the code at runtime, caching them for later re-use. 
