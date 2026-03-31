---
title: Comparison of common compression algorithms
date: 2026-03-31
tags: []
---

## Archiving vs compression

It's important to disambiguate between an archiving algorithm and a compression algorithm. 

An archiving algorithm's purpose is simply to collate multiple files into one. 

A compression algorithm, as the name suggests, reduces the size of a block of data. 

Some formats mentioned here support both archiving and compression, while others are compression-only. Generally, archiving and compression formats can be updated after creation, while compression-only formats must be rebuilt from scratch. 

## Trade-offs 

More compression means more compute. To get a higher compression ratio, you'll need to spend more time and power compressing data.  

The dictionary size (window size) determines how far back the compressor can look in order to find repeated data. A higher value means the compressor finds more long-range matches, which means a higher compression ratio for data with long repeating batterns, but makes compression and decompression slower and more costly in terms of memory. 

Increasing word size allows the compressor to find more optimal matches and capture longer repeated sequences, which is great for structured and repetetive data, though it makes compression slower and increases CPU usage. 

Solid block size controls how much data is treated as a single, continuous block. Increasing it makes for a higher compression ratio, especially across similar files, but is slower and more memory-intensive to compress and decompress. 

Generally, increasing these values yields smaller results, but takes a longer time and more system resources. This ends up with diminishing returns over time, so it's good to understand the data you're compressing and choose optimal values. 

## 7z

The 7z format is an archiving and compression format that supports the compression algorithms LZMA, LZMA2, PPMd, and BZip2. Dictionary size, solid block size, and word size (except for in BZip2) are configurable. Archives can be split into multiple volumes (filse), and can be updated after creation. 7z also supports AES-256 encryption, with file content and file name encryption being independently optional. 

7z is commonly used for backups and archival storage where compression ratio is the most important factor. 

7z is released under the GNU Lesser General Public License. 

## GZ

GZip (GZ) is a compression-only algorithm that uses the DEFLATE (hereforth "deflate", also called "Flate") compression algorithm which combines the LZ77 algorithm and Huffman coding, standardised in RFC 1951. 

While similar to Zip, GZip uses a different internal structure that is optimised for streaming, with headers and metadata at the start of the data block. This means you can begin to decompress a GZip archive before its download is complete. 

Since GZip doesn't support archive, it's often paired with Bell Labs' archive-only TAR ("Tape Archive", also known as "Tarball") format, resulting in files with the extension `.tar.gz`. 

GZip is released under the GNU General Public License 3.0. 

## RAR 

RAR is an archiving and compression format that supports a configurable dictionary size and multiple volumes. It uses a proprietary compression algorithm. 

RAR is great for distributing large files in multiple chunks, e.g. when downloading from a website. 

RAR is proprietary. A license is required, but the program WinRar famously does not enforce its license requirement for private users. 

## XZ

XZ is a compression-only format that wraps the LZMA compression algorithm. It's slower than the comparable GZip, but results in higher compression ratios. 

While it's possible to stream XZ-encoded data, it's less optimised than gzip, so only really makes sense if attempting to minimise bandwidth usage at the cost of processing time. 

Similar to GZip, XZ is commonly paired with the Tarball archiving format to make `.tar.xz` compressed archives. 

Its licensing can be confusing, with different source files released under 0BSD, GPL 2.0, GPL 3.0, and LGPL 2.1, but XZ as a whole is free and open source. 

## ZIP 

ZIP is an archiving and compression format based on the deflate algorithm supporting configurable word size and encryption with either AES-256 or ZipCrypto. 

ZIP is the most widely supported compression algorithm and generally very fast, but yields one of the weakest compression ratios. 

It is unclear which licene(s) apply to ZIP. 

## Summary 

* .ZIP is great for compatibility. 
* .RAR is great for sharing large files over HTTP. 
* .7z and .xz are great for long-term archival. 
* .gz is great for streaming. 

There's much more to compression than just the compression format. The size and frequency of repeated data blocks in the source data are also significant and can influence which compression algorithm yields the best results. For example, structures like HTML and JSON compress incredibly well due to their highly repetitive nature (often best when tuned with a small dictionary size and high solid block size), while images and video have more dissonant data and would benefit more from being converted into a different format or codec than any of these compression algorithms. 