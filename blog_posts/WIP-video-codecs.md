## Aspect ratio 



## Resolution 

A video, as presented on a computer, is simply a stream of images. Each image has a width and a height, known as its "resolution". 

Some resolutions are expressed as a whole number suffixed with "p". In this case, the number should be taken to mean the number of pixels horizontally. Others are suffixed with "K", which is a little more difficult to comprehend - 4K is 3480px wide to consumers, while "DCI 4K", used in cinemas, is 4096px wide. 

The aspect ratio of an image or video refers to the ratio of its width to its height, expressed as a ratio with the horizontal width first. Older TV screens typically used a 4:3 aspect ratio. Later televisions preferred 16:9. Some modern media is portrayed in 18:9 (also presented as 1:2), due to the removal of bezels from mobile devices. 

By using the aspect ratio and the 

## Frame rate

## Containers 

Each file type for video, such as .mp4 or .mkv, represents a container for video and audio, plus additional optional features. Both video and audio streams are encoded using a "codec", which defines how the data is stored on disk, with a trade off between quality and file size. 

MP4 (MPEG-4 Part XIV) is a partially open container format. It's defined by an ISO standard, but there are some patents related to it. It has limited support for subtitles, chapters, and multiple audio tracks. It's great for compatibility as it's supported by the majority of platforms. 

MVK (Matroska Video) is a fully open container standard with very high flexibility. It has excellent support for subtitles, multiple audio tracks, and chapters. 

AVI is a proprietary container format designed by Microsoft. These days, it's considered legacy, with very limited support for subtitling and multiple audio tracks, and no support for chapters. 

MOV is Apple's proprietary container format. It has great support for subtitles, multiple audio tracks, and chapters, and is often used by video editing professionals. 

WebM is an emerging and fully open container standard developed by Google. It has good support for subtitles and multiple audio tracks, but limited support for chapters. 

## Video codecs 

Many DVDs and other older media are encoded with the patented MPEG-2 codec, which is widely supported for playback but terribly inefficient and yields low quality results in comparison with modern alternatives. 

H.264 (AVC, Advanced Video Codec) is widely supported for playback, but subject to many patents. 

H.265 (HEVC, Highly Efficient Video Codec) is an improvement upon AVC with higher quality and compression efficiency, though it's also subject to many patents. 

VP9 (Video Processing 9) is an open standard with similarly high compression efficiency and quality, optimised for video streaming. 

AV1 (AOMedia Video 1) is an open standard that provides the best compression ratio and quality. It's compatible with relatively few devices, but support continues to grow. 

## Audio Codecs 

MP3 (MPEG-1 Audio Layer III) is a low-efficiency lossy audio codec with an expired patent. It's supported nearly everywhere, but delivers relatively terrible quality. 

AAC (Advanced Audio Coding) is a slight improvement upon MP3. It remains lossy, but has a higher quality and efficiency, though it is subject to patents. 

Opus is a high-quality lossy codec with an open standard. Its main benefit is its low latency, which makes it better suited for real-time voice communications than media playback. 

FLAC (Free Lossless Audio Codec) is a lossless, high-quality, high-efficiency codec with an open standard. It's the option for retaining full quality in audio. Apple has a variant, ALAC (Apple Lossles Audio Codec), used in their own ecosystem. 

## Support Comparison

Legend: 
- `Y` - Supported
- `N` - Not supported
- `L` - Limited support

Higher quality codecs are presented further towards the right. More versatile containers are presented further towards the bottom. 

### Video 

| Container x Codec | MPEG-2 | H.264 (AVC) | H.265 (HEVC) | VP9 | AV1 | 
| --- | --- | --- | --- | --- | --- | 
| WebM | N | N | N | Y | Y | 
| AVI | Y | L | L | N | N | 
| MOV | Y | Y | Y | N | L | 
| MP4 | Y | Y | Y | L | Y | 
| MKV | Y | Y | Y | Y | Y | 

### Audio 

| Container x Codec | MP3 | AAC | Opus | FLAC | ALAC |
| --- | --- | --- | --- | --- | --- |
| WebM | N | N | Y | N | N |
| AVI | Y | Y | N | N | N |
| MOV | Y | Y | N | N | Y |
| MP4 | Y | Y | L | N | Y |
| MKV | Y | Y | Y | Y | Y |

## Summary

The most versatile container option is MKV. 