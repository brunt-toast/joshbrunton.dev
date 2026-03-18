---
title: Variance in C# generic type parameters
date: 2026-03-18
tags: [C#]
---

## Default behaviour

The default variance for a generic type parameter in C# is invariant. This means that it's legal for some parameter, `T`, to appear as an argument, return type, or both. In other words, there are no restrictions on what you can do with that type parameter. 

The reason for this is simple: unless told otherwise, the compiler assumes that `IInvariant<T>` will use `T` as both a method argument and a return type. 

If `T` is used as a method argument, you can't use a less derived type ("widening" or "upcasting"), because the less derived type might lack a property or method that the interface relies on. For example, `MemoryStream` has a property `Capacity`, but its base claass `Stream` doesn't. 

If `T` is used as a return type, you can't use a more derived type ("narrowing" or "downcasting"), because you can't guarantee a conversion to a more derived type. For example, not every `Stream` is a `MemoryStream`.

In practice, this means that you can't just assign an `IInvariant<T>` to an `IInvariant<TBase>` or an `IInvariant<TDerived>` (where `TDerived : T` and `T : TBase`).

```csharp 
interface IInvariant<T>;

IInvariant<Stream> stream = /* ... */;
IInvariant<MemoryStream> memoryStream = stream; // Error! We can't move towards a more derived type, because the streams in IInvariant<Stream> might not be MemoryStreams. 

IInvariant<MemoryStream> memoryStream = /* ... */;
IInvariant<Stream> stream = memoryStream; // Error! We can't move towards a less derived type, because the implementation of IInvariant<MemoryStream> might rely on MemoryStream.Capacity. 
```

C# discourages this because these casts may be invalid or break the implementation, leading to unexpected exceptions. To make these assignments work, you'd have to explicitly cast the right hand side to the new variable's type. This requires extra syntax, and warrants extra safety checks. 

To save ourselves from writing all this extra code, we can declare generic parameters as co-variant or contra-variant where appropriate. This enables implicit casts and promises that they'll succeed 100% of the time. 

## Covariant parameters 

In the below example, we try to assign an `IInvariant<MemoryStream>` to an `IInvariant<Stream>`. Since `T` is invariant, and `Stream` is less derived than `MemoryStream`, we get a compiler error, because `IInvariant` might be relying on properties or methods unique to `MemoryStream`. 

```csharp
interface IInvariant<T>;
IInvariant<MemoryStream> memoryStream = /* ... */;
IInvariant<Stream> stream = memoryStream; // Error! CS0266
```

Instead, let's try making `T` covariant. Because promise the compiler that it's safe to treat `ICovariant<MemoryStream>` as `ICovariant<Stream>`, the assignment is accepted without any explicit cast. 

```csharp
interface ICovariant<out T>;
ICovariant<MemoryStream> memoryStream = /* ... */;
ICovariant<Stream> stream = memoryStream; // Works great!
```

## Contravariant parameters

Contravariant parameters are simply the opposite of covariant parameters. They promise that they will only be ever used as method arguments; never as a return type. This means we can assign them to a more derived type. 

By default, with an invariant parameter, this assignment is illegal:

```csharp
interface IInvariant<T>;
IInvariant<Stream> stream = /* ... */ ;
IInvariant<MemoryStream> memoryStream = stream; // Error! CS0266
```

But when we make `T` contravariant: 

```csharp
interface IContravariant<in T>;
IContravariant<Stream> stream = /* ... */ ;
IContravariant<MemoryStream> memoryStream = stream; // Perfectly fine!
```

## Constraints 

Variance can only specified on interfaces and delegate types, not classes or structs. This is because interfaces and delegates are behavioural contracts and don't have any state or logic. An implementation could break the promise of variance in a way that the compiler isn't advanced enough to check. 