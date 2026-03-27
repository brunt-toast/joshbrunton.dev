---
title: What is SecureString, anyway? 
date: 2026-02-17
tags: [Security, .NET]
---

SecureString (`System.Security.SecureString`) is a class designed to add a measure of security to string and string-like content in .NET. 

## Implementation 

A regular System.String is allocated on the heap, and is immutable. This means that you can never know when it will be garbage collected, and just overwriting its value does nothing to destroy the original from memory. SecureString, despite being a reference type, stores its value in a way that can be purged from memory on demand, by calling its `.Dispose()` method. On Windows with .NET Core, the contents of a SecureString are also encrypted. 

The maximum length of a SecureString is 65,536 ($2^{16}$) characters, which translates to a maximum in-memory size of 131.126KiB for the underlying value, plus overhead for properties on the class. This is length is set by a private const in the SecureString class, and the length is bounds checked on modification, throwing an `ArgumentOutOfRangeException` if it gets too long. 

## Building a SecureString 

SecureString shouldn't be created from a string or other immutable reference type, because if data is assigned to a string, it's already defeated the point. Instead, it should be fed by a stream, or another char-by-char source such as a loop over Console.ReadKey(). 

The SecureString can be built by calling .AppendChar(char), which adds one character at a time. This API disincentivises feeding SecureString with a plain string. Remember to handle `ArgumentOutOfRangeException` in case the number of characters exceeds the limit. 

Once a SecureString has finished building, you can call .MakeReadOnly(). Trying to modify the value after this will throw an `InvalidOperationException`. 

## Using a SecureString 

Some libraries expose APIs accepting a SecureString. If you need to consume the value of a SecureString yourself, you can use the following method adapted from the System.Net.NetworkCredential class in .NET 10.0.100 SDK. 

```csharp
static string MarshalToString(SecureString sstr)
{
    if (sstr.Length == 0)
    {
        return string.Empty;
    }

    IntPtr ptr = IntPtr.Zero;
    string result;
    try
    {
        ptr = Marshal.SecureStringToGlobalAllocUnicode(sstr);
        result = Marshal.PtrToStringUni(ptr)!;
    }
    finally
    {
        if (ptr != IntPtr.Zero)
        {
            Marshal.ZeroFreeGlobalAllocUnicode(ptr);
        }
    }
    return result;
}
```

## Limitations 

The SecureString class doesn't expose itself or its properties to the Component Object Model, meaning other components can't query it. The C# definition is also not entirely CLS compliant, meaning it's not guaranteed to be interoperable with other .NET lanaguges. 

Even Windows doesn't have a secure string implementation at the OS level. This means that in order to use the secure string, it must live un-encrypted in memory, however briefly. SecureString only reduces the window of time a sensitive value spends in memory, it does not eliminate it. Because of this, analyzer rule DE0001 suggests that SecureString should be avoided in favour of certificates or OS-level authentication. 

## Extra: Turning a string into a SecureString, the evil way

While it's inadvisable to feed a SecureString from a string, sometimes you just don't care. Maybe an API will only accept a SecureString, but you don't care so much about securing the value that feeds it. 

Instead of looping over a string and using `.AppendChar()` repeatedly, conversion can be made cleaner with extension method, such as the one below, which takes $194.674\mu s\pm0.5811\mu s$ for a 50-character string on a 3.7GHz processor). 

```csharp
static SecureString ToSecureString(this string source)
{
    var ret = new SecureString();
    foreach (char c in source)
    {
        ret.AppendChar(c);
    }
    ret.MakeReadOnly();
    return ret;
}
```

Or this C-like monstrosity (with compiler flag `/p:AllowUnsafeBlocks=true`). The below method is significantly faster, taking only $7.700\mu s\pm 0.0533\mu s$ for a 50-char string. Note that `OverflowException` may be thrown for strings longer than 65,536 characters, instead of the usual `ArgumentOutOfRangeException` thrown by `.AppendChar()`). 

```csharp
static unsafe SecureString ToSecureString(this string source)
{
    fixed (char* charPtr = source)
    {
        ushort len = 0;
        do {} while (charPtr[++len] != '\0');

        return new SecureString(charPtr, len * sizeof(char));
    }
}
```

## References

https://learn.microsoft.com/en-us/dotnet/fundamentals/runtime-libraries/system-security-securestring

https://github.com/dotnet/platform-compat/blob/master/docs/DE0001.md

https://stackoverflow.com/questions/1570422/convert-string-to-securestring
