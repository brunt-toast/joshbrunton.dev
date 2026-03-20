GUID v7 is an implementation of GUID which encodes a timestamp, making numeric order synonymous with time order while still making collisions incredibly unlikely and remaining fully backwards-compatible with existing APIs accepting GUIDs. 

The method `Guid.CreateVerion7()` (and overloads) was added to the .NET standard library in version 9, but to this day with .NET 10 in LTS and .NET 11 in preview, there are no methods to read the timestamp component of a GUID v7.

This article details how to identify a GUID v7 and parse out its timestamp, using some monstrous C-like (but safe!) code that directly addresses bits in memory. 

## Identifying a GUID v7

As with all GUIDs, the first 4 bits 9th byte's firt bits. For v7, the variant specifies that the 9th byte's first bits must be `0b10`. Additionally, in a GUID v7, The 7th byte's first bits must be `0b0111`, to indicate the version number. 

As a result of these properties and the GUID specification in general, you can check for sure whether a GUID is version 7 using bit masking. Mathematically speaking, for a GUID v7, the following two must be true (and, conversely, one or both must be false for a non-v7 GUID):

$$
b_7 \land 11110000 = 01110000
$$

$$
b_8 \land 11000000 = 10000000
$$

We can use these rules to create a very efficient C# method to check if a GUID is v7 or not. This method runs in $O(n)$ time with zero heap allocations, taking an average of $216.0ns\pm 6.77ns$ on a 3.7GHz processor. 

```csharp
static bool IsVersion7(Guid id)
{
    Span<byte> bytes = stackalloc byte[16];
    id.TryWriteBytes(bytes);

    return (bytes[7] & 0b11110000) == 0b01110000
        && (bytes[8] & 0b11000000) == 0b10000000;
}
```

We'll re-use this logic later when sanity checking our inputs. 

## Extracting a DateTimeOffset from a GUID v7

If we copy the first 48 bits of a GUID v7 into a `long`, we can then use that long to generate a `DateTimeOffset`. 

The GUID v7 specification indicates that the first 48 bits are the number of milliseconds elapsed since the UNIX epoch. It also defines an optional extra 12 bits to indicate sub-millisecond accuracy. Since `DateTimeOffset`'s maximum granularity is $100ns$ (a "tick"), and GUID v7's is $244.140625ns$, we can use `DateTimeOffset` it to full range of timestamps available to GUID v7. 

>[!NOTE]
> `Guid.CreateV7(DateTimeOffset timestamp)` doesn't use the optional sub-millisecond accuracy. If you need to test for this level of granularity, you'll need to hand-craft your input data. 

In the below implementation, we use the `TryParse` pattern as an extension of return type `DateTimeOffset`. We do this instead of making an extension `Guid.ToDateTimeOffset()` because for robustness, we must assume that the following failure conditions are possible:

* `id.TryWriteBytes` might fail (in practice, it won't, because we know for a fact that 16 bytes of memory is exactly right, but the API suggests it might) 
* The GUID might not be v7 
* The timestamp component might fall outside the bounds of an acceptable value for `DateTimeOffset.FromUnixTimeMilliseconds` 

This method runs in $O(n)$, should never throw an exception, and will make no allocations to the heap. On a 3.7GHz processor, it takes an average of $134.4ns\pm19.29ns$. 

>[!NOTE]
> Because of compiler optimisations, this method runs faster than our earlier `Guid.IsVersion7()`, despite wrapping its logic.

```csharp
extension(DateTimeOffset)
{
    public static bool TryParseGuidV7(Guid id, out DateTimeOffset ret)
    {
        Span<byte> b = stackalloc byte[16];

        if (!id.TryWriteBytes(b, true, out _)
            || (b[6] & 0b11110000) != 0b01110000
            || (b[8] & 0b11000000) != 0b10000000)
        {
            ret = default;
            return false;
        }

        long raw = BinaryPrimitives.ReadInt64BigEndian(b);
        long ticks = 621355968000000000
                        + (raw >> 16) * 10_000
                        + (((raw & 0x0FFF) * 10_000) >> 12);

        if (ticks is < 0 or > 3155378975999999999)
        {
            ret = default;
            return false;
        }

        ret = new DateTimeOffset(ticks, TimeSpan.Zero);
        return true;
    }
}
```

## Closing Thoughts 

With these methods, it should be easy and reliable to extract timestamp info from GUIDs for presentation and manipulation. 

Now, we won't be tempted to keep our `CreatedAt datetime` database columns for the convenience of not having to extract the timestamp (at the cost of query and write speed). 

## References 

https://datatracker.ietf.org/doc/rfc9562/