In .NET, `Guid.CreateVersion7()` ignores the optional sub-millisecond precision allowed for by RFC 9562. This post details how to increase the maximum precision from 1ms to 2.44140625ns. And, of course, with zero allocations to the managed heap.

## Starting Out 

RFC 9562 §6.9 states that "Implementations **SHOULD** utilize a cryptographically secure pseudorandom number generator". 

Some investigation into the file `src/runtime/src/libraries/System.Private.CoreLib/src/System/Guid.cs` in the .NET monorepo shows that under the hood, `Guid.CreateVersion7()` wraps `Guid.NewGuid()`, which farms out responsibility for the CSPRNG to the system. 

To keep this security, we'll start with a span of bytes containing a random GUID from the existing implementation. 

```csharp
static Guid CreateVersion7Precise(DateTimeOffset d)
{
    Span<byte> bytes = stackalloc byte[16];
    _ = Guid.NewGuid().TryWriteBytes(bytes);
    
    // ...
}
```

>[!NOTE]
> We don't expect `TryWriteBytes()` to fail here. As of time of writing, the only reason it would fail is if `bytes` didn't have enough space, but we know that `Guid.NewGuid()` and the later used `Guid.CreateVersion7()` will always be exactly 16 bytes.

## Setting the millisecond-precision timestamp 

Our next point of business is encoding the timestamp with millisecond-level precision. 

If using .NET 8 or lower, we'd have to do this manually. The below example demonstrates the appropriate mapping in case you're subject to this limitation.  

```csharp
long totalMilliseconds = d.ToUnixTimeMilliseconds();
bytes[3] = (byte)(totalMilliseconds >> 0x28);
bytes[2] = (byte)(totalMilliseconds >> 0x20);
bytes[1] = (byte)(totalMilliseconds >> 0x18);
bytes[0] = (byte)(totalMilliseconds >> 0x10);
bytes[5] = (byte)(totalMilliseconds >> 0x08);
bytes[4] = (byte)(totalMilliseconds);
```

But with .NET 9.0 and greater, we can farm this out to the existing `CreateVersion7()` method instead.

```csharp
Span<byte> bytes = stackalloc byte[16];
_ = Guid.CreateVersion7(d).TryWriteBytes(bytes);
```

.NET framework and standard don't support `Guid.TryWriteBytes()`. You'll need to use `.ToByteArray()` instead, which will cause a heap allocation. 

## Setting the fractional component 

Next up, we need to compute the fraction of a millisecond that the remaining ticks represent. While there are 10,000 ticks in a millisecond, GUID v7 has a maximum precision of 1/4096 of a millisecond (equal to 2.44140625ns). 

Mathematically speaking, the denominator of this fraction is 4096, and the numerator is defined as: 

$$
n = {{min(\lfloor{{({\Delta_{ticks}\cdot4096}) + 5000}\over10000}\rfloor, 4095)}}
$$

In code, we can express that like so:

```csharp
int fracNumerator = (int) Math.Min((d.Ticks % 10000 * 4096 + 5000) / 10_000, 4095);
```

Then, we can update our Guid like so: 

```csharp
bytes[6] = (byte)(fracNumerator & 0xFF);
bytes[7] = (byte)((fracNumerator >> 8) & 0x0F);
```

## Repairing the version 

Finally, since we've just overwritten the 8th byte (which is shared between the version number and the fractional component), we need to put its first nibble back to 7. We can do this with some simple bit logic.

```csharp
bytes[7] = (byte)((bytes[7] & 0x0F) | 0x70);
```

## Complete method 

Putting all this together, our complete method for enhanced precision GUID v7 generation in .NET 9.0 and greater is:

```csharp
static Guid CreateVersion7Precise(DateTimeOffset d)
{
    Span<byte> bytes = stackalloc byte[16];
    _ = Guid.CreateVersion7(d).TryWriteBytes(bytes);

    int fracNumerator = (int) Math.Min((d.Ticks % 10000 * 4096 + 5000) / 10_000, 4095);
    bytes[6] = (byte)(fracNumerator & 0xFF);
    bytes[7] = (byte)((fracNumerator >> 8) & 0x0F);

    bytes[7] = (byte)((bytes[7] & 0x0F) | 0x70);

    return new Guid(bytes);
}
```

For .NET Core 8 and lower: 

```csharp
public static Guid CreateVersion7Precise(DateTimeOffset d)
{
    Span<byte> bytes = stackalloc byte[16];
    Guid.NewGuid().TryWriteBytes(bytes);

    long totalMilliseconds = d.ToUnixTimeMilliseconds();
    bytes[3] = (byte)(totalMilliseconds >> 0x28);
    bytes[2] = (byte)(totalMilliseconds >> 0x20);
    bytes[1] = (byte)(totalMilliseconds >> 0x18);
    bytes[0] = (byte)(totalMilliseconds >> 0x10);
    bytes[5] = (byte)(totalMilliseconds >> 0x08);
    bytes[4] = (byte)(totalMilliseconds);

    int fracNumerator = (int)Math.Min((d.Ticks % 10000 * 4096 + 5000) / 10_000, 4095);
    bytes[6] = (byte)(fracNumerator & 0xFF);
    bytes[7] = (byte)((fracNumerator >> 8) & 0x0F);

    bytes[7] = (byte)((bytes[7] & 0x0F) | 0x70);

    return new Guid(bytes);
}
```

And finally, for .NET standard: 

```csharp
public static Guid CreateVersion7Precise(DateTimeOffset d)
{
    byte[] bytes = Guid.NewGuid().ToByteArray();

    long totalMilliseconds = d.ToUnixTimeMilliseconds();
    bytes[3] = (byte)(totalMilliseconds >> 0x28);
    bytes[2] = (byte)(totalMilliseconds >> 0x20);
    bytes[1] = (byte)(totalMilliseconds >> 0x18);
    bytes[0] = (byte)(totalMilliseconds >> 0x10);
    bytes[5] = (byte)(totalMilliseconds >> 0x08);
    bytes[4] = (byte)(totalMilliseconds);

    int fracNumerator = (int)Math.Min((d.Ticks % 10000 * 4096 + 5000) / 10_000, 4095);
    bytes[6] = (byte)(fracNumerator & 0xFF);
    bytes[7] = (byte)((fracNumerator >> 8) & 0x0F);

    bytes[7] = (byte)((bytes[7] & 0x0F) | 0x70);

    return new Guid(bytes);
}
```

## Testing consideration

Since GUID v7 can't express the full range of ticks, this method has a margin of error of $\pm2$ ticks, or $\pm200ns$.When testing, the success condition is: 

$$
|ticks_1 - ticks_2| \le 2
$$

Or, in code: 

```csharp
Math.Abs(left.Ticks - right.Ticks) <= 2;
```
