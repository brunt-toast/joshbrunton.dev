GitHub user and [FastGuid](https://github.com/sdrapkin/SecurityDriven.FastGuid) developer [Stan Drapkin](https://github.com/sdrapkin/) siggests in a [gist](https://gist.github.com/sdrapkin/03b13a9f7ba80afe62c3308b91c943ed) that we should avoid using `Guid.CreateVersion7()` in .NET. They point out that the UUID standard, [RFC 9562](https://www.ietf.org/rfc/rfc9562.pdf), requires that the unix_ts_ms component of a GUID must be in big-endian format (§5.7). 

§4 of the RFC points out that "there is a known caveat that Microsoft's Component Object Model (COM) GUIDs leverage little-endian when saving GUIDs", pointing to Raymond Chen's aritlce, [*Why does COM express GUIDs in a mix of big-endian and little-endian? Why can't it just pick a side and stick with it?*](https://devblogs.microsoft.com/oldnewthing/20220928-00/?p=107221). This ordering applies to *all* GUIDs, rather than being a symptom of how v7 is generated. We're only now starting to notice because v7 has a predictable order.

Drapkin shows that when dumped as its raw memory, a GUID v7 has no less fragmentation than any other GUID implementation, resulting in 35% larger database indices and 20% worse page density compared to a version with RFC-compliant big-endian byte order. 

Honestly, they make a good point. v7s are meant to be optimised to be stored as opaque raw bytes to minimise fragmentation (§6.11). The .NET implementation falls short of this goal. 

So, how do we get around this? 

If we don't need to optimise for storage, we could encode the GUID as text. Sometimes that's preferable, e.g. in SQLite (which doesn't have a native GUID type and therefore is much easier to read and query as text), but it's wasteful: a GUID expressed in 36 characters requires at least 36 bytes of storage, compared to the 16 bytes of data it actually encodes, so more than 50% of the space is spent on impossible values. 

We could, of course, use FastGuid, as Drapkin suggests. It does have its merits! It's significantly faster than the .NET standard libraries, and integrates with the .NET GUID type. However, you then need to remember to use `FastGuid.NewGuid()` for GUIDs, and end up encoding infrastructure details if using `.NewSqlServerGuid` or `.NewPostgreSqlGuid`. These don't really push you into the pit of success. 

Instead, we can fully optimise for storage space and defragmentation in a database-agnostic fashion while keeping our standard library APIs by defining conversions between RFC and CLR ordering and establishing a convention within an entity framework context. 

## Converting a GUID to a big-endian byte array 

To turn a CLR-order memory span into an RFC-order memory span, we can copy the GUID into a new span of memory, then swap the relevant bytes. This takes an average of only $1\mu s$ and allocates 40 bytes. 

```csharp
static byte[] ToBigEndianByteArray(Guid id)
{
    Span<byte> bytes = stackalloc byte[16];

    id.TryWriteBytes(bytes);

    (bytes[0], bytes[3]) = (bytes[3], bytes[0]);
    (bytes[1], bytes[2]) = (bytes[2], bytes[1]);
    (bytes[4], bytes[5]) = (bytes[5], bytes[4]);
    (bytes[6], bytes[7]) = (bytes[7], bytes[6]);

    return bytes.ToArray();
}
```

Compared to a similar implementation which achieves the same effect by converting the GUID to a string and then parsing it into bytes, this is 77% faster and 98% more memory efficient.

## Converting a big-endian byte array to a GUID  

The GUID constructors still expect bytes in COM order. To parse a big-endian byte array back into a GUID object, we'll need a custom factory method. 

The logic here is simple. Since the mapping we applied arlier is a self-inverse operation, we can apply it again to restore the COM endian order, and feed it back to the default constructor. This has 0 allocation and takes around 450ns. 

```csharp
static Guid FromBigEndianByteArray(byte[] bytes)
{
    Span<byte> byteSpan = stackalloc byte[16];
    bytes.CopyTo(byteSpan);

    (byteSpan[0], byteSpan[3]) = (byteSpan[3], byteSpan[0]);
    (byteSpan[1], byteSpan[2]) = (byteSpan[2], byteSpan[1]);
    (byteSpan[4], byteSpan[5]) = (byteSpan[5], byteSpan[4]);
    (byteSpan[6], byteSpan[7]) = (byteSpan[7], byteSpan[6]);

    return new Guid(byteSpan);
}
```

## Configuring an Entity Framework context 

To convince the EF context to use our big-endian byte order, we'll first need to define a value converter class used to swap between our CLR Guid and the desired byte array. 

```csharp
class GuidToBigEndianByteArrayConverter()
    : ValueConverter<Guid, byte[]>(
        g => g.ToBigEndianByteArray(),
        b => Guid.FromBigEndianByteArray(b));
```

Then, in our DBContext, we configure the conversion as a convention using an override method. 

```csharp
protected override void ConfigureConventions(ModelConfigurationBuilder builder)
{
    builder
        .Properties<Guid>()
        .HaveConversion<GuidToBigEndianByteArrayConverter>();
}
```

By default, this will choose the same column type as would be used for a `byte[]`. If you know your database provider, you can use a custom column type, perhaps with a fixed length for improved performance, by chaining `.HaveColumnType("BINARY(16)")` (example type valid for Microsoft SQL Server). 

## Performance consideration

I compared the performance of the default behaviour and the adjusted behaviour on a SQLite database. The default type for a GUID in SQLite is TEXT, and the type assigned to byte[] is BLOB. Despite introducing more work to smudge and clean our GUIDs, the adjusted version was on average 2% faster and 17% more memory efficient. 

Mileage may vary with other providers, but I don't have the time or resources to test every major database. This SQLite test, though, should serve as a good indicator that the performance impact is negligible at worst and positive at best. 

## Conclusion 

Now that we've set this up, we can continue to use the standard `Guid.CreateVersion7()` API while eliminating the database fragmentation problems caused by the COM GUID byte order. 
