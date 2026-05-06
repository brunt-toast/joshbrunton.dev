This method is consistently 13-24% faster, and uses 44-58% less memory, than a comparative method using `Encoding.GetBytes`. 

```csharp
static string Hash(this string source, HashAlgorithm algorithm)
{
    int maxByteCount = Encoding.UTF8.GetMaxByteCount(source.Length);
    Span<byte> inputBytes = stackalloc byte[maxByteCount];
    int actualByteCount = Encoding.UTF8.GetBytes(source, inputBytes);

    Span<byte> hashBytes = stackalloc byte[algorithm.HashSize / 8];

    algorithm.TryComputeHash(
        inputBytes[..actualByteCount],
        hashBytes,
        out int bytesWritten);

    return Convert.ToHexString(hashBytes[..bytesWritten]);
}
```
