GUID v7 is an implementation of GUID which encodes a timestamp, making numeric order synonymous with time order while still making collisions incredibly unlikely and remaining fully backwards-compatible with existing APIs accepting GUIDs. 

The method `Guid.CreateVerion7()` (and overloads) was added to the .NET standard library in version 9, but to this day with .NET 10 in LTS and .NET 11 in preview, there are no methods to read the timestamp component of a GUID v7. 

This article details how to identify a GUID v7 and parse out its timestamp, using some monstrous C-like C# code. 

## Identifying a GUID v7

As with all GUIDs, the first 4 bits 9th byte's firt bits. For v7, the variant specifies that the 9th byte's first bits must be `0b10`. Additionally, in a GUID v7, The 7th byte's first bits must be `0b0111`, to indicate the version number. 

As a result of these properties and the GUID specification in general, you can check for sure whether a GUID is version 7 using bit masking. Mathematically speaking, for a GUID v7, the following two must be true (and, conversely, one or both must be false for a non-v7 GUID):

$$
b_7 \land 11110000 = 01110000
$$

$$
b_8 \land 11000000 = 10000000
$$

We can use these rules to create a very efficient C# method to check if a GUID is v7 or not. This method runs in O(n) time with zero heap allocations, taking an average of $216.0ns\pm 6.77ns$ on a 3.7GHz processor. 

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

In the below implementation, we use the `TryParse` pattern as an extension of return type `DateTimeOffset`. We do this instead of making an extension `Guid.ToDateTimeOffset()` because for robustness, we must assume that:

* `id.TryWriteBytes` might fail (we know we have enough memory, but it's good to treat it as the API contract intends)
* The GUID might not be v7
* The timestamp component might fall outside the bounds of an acceptable value for `DateTimeOffset.FromUnixTimeMilliseconds`

Note that the assignment of the variable `timestamp` looks odd here because the byte order for `Guid` and `long` in .NET are different. 

This method runs in O(n), should never throw an exception, and will make no allocations to the heap. On a 3.7GHz processor, it takes an average of $1.314\mu s\pm0.0298\mu s$. 

```csharp
extension(DateTimeOffset)
{
  public static bool TryParseGuidV7(Guid id, out DateTimeOffset ret)
  {
      const long dateTimeOffsetMinValue = -62135596800000;
      const long dateTimeOffsetMaxValue = 253402300799999;

      Span<byte> b = stackalloc byte[16];
      long timestamp;

      if (!id.TryWriteBytes(b)
          || (b[7] & 0b11110000) != 0b01110000
          || (b[8] & 0b11000000) != 0b10000000)
      {
          ret = default;
          return false;
      }

      timestamp =
          ((long)b[3] << 0x28) |
          ((long)b[2] << 0x20) |
          ((long)b[1] << 0x18) |
          ((long)b[0] << 0x10) |
          ((long)b[5] << 0x8) |
          b[4];

      if (timestamp is < dateTimeOffsetMinValue or > dateTimeOffsetMaxValue)
      {
          ret = default;
          return false;
      }

      ret = DateTimeOffset.FromUnixTimeMilliseconds(timestamp).DateTime;
      return true;
  }
}
```