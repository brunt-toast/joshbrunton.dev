---
title: Double, Float, or Decimal?
date: 2026-02-03
tags: [C#, .NET]
---

`double`, `float`, and `decimal` are all C# aliases for simple .NET value types which represent real numbers, but it's not immediately clear the difference between them, or which one you should be using. 

This article explains the bit-by-bit differences of the three types, as well as their use cases and important considerations when working with them. 

## Mathematical Theory

A floating-point number expressed in binary is similar to the standard or index form in base 10. 

In index form, can express any real number as some value greater than or equal to 1 and less than 10 (the "mantissa" `m`), multiplied by 10 (the base `b`) to the power of an integer (the "exponent" `e`), or `m(b^e)` for `1 <= m < 10` and `e % 1 = 0`. This is commonly used in fields such as physics to express very large or very small values without writing "0" too many times.

A floating point number is similar, having a mantissa and an exponent, and being expressed as `m(b^e)`, but we don't place any constraints upon the value of the mantissa. This means that we have to choose how many bits are allocated for the mantissa, and how many are for the exponent. 

Some fractional values cannot be truly expressed in binary because they are irrational (i.e., have infinite precision). The same is true of base 10 (e.g. 1/3), but it's not always the same fractions that can't be precisely expressed. 

When expressing real numbers with a fixed number of bits, there has to be a trade off between range and precision. The more bits are allocated to the mantissa, the more precision you can get (i.e. the higher the number of decimal places you can distinguish). The more bits allocated to the exponent, the higher the range of values you can express. It's important to find a good ratio of mantissa to exponent bits to balance range and precision. We can "score" a type's precision by taking the ratio of mantissa to exponent, with higher values representing higher precision. 

## Underlying Types

The C# keyword `float` is compiled down to `global::System.Single`. It spans 32 bits of memory, with a 23 bit mantissa, 8 bit exponent, and single bit for the sign. It has a range of roughly +-3.4*10^38, and an adressable precision of 7 decimal places (though 9 are maintained internally). 

The `double` keyword aliases to `System.Double`. It is effectively a double-precision float, spanning 64 bits of memory with 52 bits of mantissa and 10 bits of exponent (plus a spare bit for the sign), for a range of about +-1.8*10^308. It has a maximum precision of 15 addressable digits, though 17 are kept internally.

`decimal` aliases to `System.Decimal`. It is comprised of 128 bits, with a 96-bit mantissa and 5 bits of exponent (though only values 0-28 are valid), plus a bit for the sign. The documentation only states that the 32 bits that are not the mantissa represent "things such as the sign and scaling factor used to specify what portion of it is a decimal fraction", so we can determine that the length of the exponent and existence of the sign bit based on the minimum and maximum values; this leaves 26 bits whose purpose is unknown. The key difference of the decimal is that its value is computed with `b=10`, rather than `b=2`. 

## Literals

When the specific type of an expression is implicit (e.g. when using `var` or assigning to `object`), a real literal with a decimal point will be treated as a `double`. 

If you need a literal to be of a different type, but can't modify anything other than the literal, you can use the type's relevant suffix: 

* `d` (or `D`) causes the literal to be treated as a `double`
* `f` (or `F`) causes the literal to be treated as a `float`
* `m` (or `M`) causes the literal to be treated as a `decimal`

## Conversion &amp; Casting

Only one implicit conversion exists between the three types, from `float` to `double`. This is because the range of values of `double` is a subset of the range of values for `float`, meaning that the cast is always safe and will never throw an exception. 

For any other conversion, you have to use an explicit cast, e.g. `(float)0.1d`. It's important to remember that this isn't guaranteed to succeed - it can throw an exception at runtime, which is important to consider. 

## Infinities &amp; NaN 

Both `float` and `double` (but not `decimal`) expose: 
* `PositiveInfinity`, defined as `1/0`, which is greater than every value other than itself;
* `NegativeInfinity`, defined as `(-1)/0` and smaller than every value other than itself
* `NaN` (Not-A-Number), `0/0`, which is not greater than, less than, or equal to anything, not even itself. 

## Rounding Error Considerations

Generally, it's considered fine to use the default equality comparison, especially on `decimal` values, but occasionally you'll run into a scenario when two values that should be equal aren't - for example, `3m * (1m / 3m) == 0.333...`.

You can compensate somewhat for imprecision when checking equality by using `Math.Abs(a - b) < t`, where `t` is your tolerance, the maxmimum expected deviation such that you won't accidentally equate two values that are meaningfully different in your use case. 

A good value for tolerance depends highly on the number and nature of operations performed on the data since it was created. 

## Performance Considerations

It's quite rare that a developer needs to care about performance when choosing real types, but sometimes, e.g. at massive scale or on very low-power hardware, it starts to matter. 

All of these types are stack-allocated value types. This means that memory equal to their size will be allocated each time they are passed to a method, but that they won't stick around after their stack frame is popped and won't need to be garbage collected. 

The `decimal` type is marginally slower to operate upon than `float` or `double`, because of it being a decimal number rather than a binary one. If precision doesn't matter, prefer a binary type in performance-critical scenarios. 

## Use Cases 

Remembering how we score an implementation's range vs its precision, `float`/`Single` has a mantissa:exponent ratio (precision score) of 2.875, while `double` has a ratio of 5.2; `decimal` dwarfs both of these with a value of 19.2. This makes `double` incredibly precise, minimising rounding errors. 

This makes `decimal` great for values which are naturally exact, such as currency or score, and where you need to minimise rounding errors. It's also good for fractions which can be expressed nearly in decimal but not so well in binary, e.g. `1/5`. 

`float` and `double` are better for values where precision is less important than range, especially in performance-critical scenarios. 

## References

https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/builtin-types/floating-point-numeric-types

https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/operators/type-testing-and-cast#cast-expression

https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/language-specification/conversions

https://learn.microsoft.com/en-us/dotnet/fundamentals/runtime-libraries/system-single

https://learn.microsoft.com/en-us/dotnet/fundamentals/runtime-libraries/system-double

https://learn.microsoft.com/en-us/dotnet/fundamentals/runtime-libraries/system-decimal
