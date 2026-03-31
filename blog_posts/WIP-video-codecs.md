There's a *lot* that goes into storing a video, far more than most people ever need to think of. It's quite complicated to learn about, so here's the introduction I wish I had when I started out with video archival. 

## Resolution 

A video, as presented on a computer, is simply a stream of images. Each image has a width and a height, known as its "resolution". 

Some resolutions are expressed as a whole number suffixed with "p" (for "progressive scan"). In this case, the number should be taken to mean the number of pixels vertically. The number of horizontal pixels is usually calculated as the ratio 16:9 (with 9 being the vertical aspect).

Numbers suffixed with "K" are interpreted differently based on whether using "Ultra High Definition" (UHD) or Digital Cinema Initiatives (DCI) measures. 1K is always 540px high, but in UHD, the width is calculated at 16:9, while DCI ratios can vary. 

A higher total pixel count means higher quality, but also that there's more data to store. 

This table breaks down common aspect ratio names. 

| Name | Aliases | Aspect ratio | Dimensions (px) | Pixel count |
| --- | --- | --- | --- | --- |
| Quarter Video Graphics Array | QVGA | 4:3 | 320 x 240 | 76,800
| Video Graphics Array | VGA | 4:3 | 640 x 480 | 307,200 |
| Standard Definition | SD, 480p | 16:9 | 720 x 480 | 345,600 | 
| High Definition | HD, 720p | 16:9 | 1280 x 720 | 921,600 |
| Full High Definition | FHD, 1080p | 16:9 | 1920 x 1080 |
| Consumer 4K | UHD 4K | 16:9 | 3840 x 2160 | 2,073,600 |
| Cinema 4K | DCI 4K | Variable | variable x 2160 | variable |
| Consumer 8K | UHD 8K | 16:9 | 7680 x 4320 | 33,177,600 |
| Cinema 8K | DCI 8K | Variable | variable x 4320 | variable | 

## Frame rate

As previously mentioned, a video is just a series of images in rapid succession. The "frame rate" of the video represents how many individual images are displayed each second. It's measured in "Hertz" (Hz), meaning "number of occurences per second". A higher value makes for a smoother video with less motion blur, but takes more space. 

Movies are generally filmed in 24Hz, though some differ from this as stylistic choices. 

Analog TV uses either 50Hz (in PAL/Phase Alternating Line regions), or 59.54Hz (in NTSC/National Television System Committee regions). 

Digital TV is transmitted at 30 or 60Hz for ATSC (Advanced Television Systems Committee) regions, and 25 or 50Hz for DVB (Digital Video Broadcasting) regions. 

## Colours 

Colour is incredibly complex. Colours are defined using primaries, transfer functions, and matrices, and subtle differences can mess up the brightness, contrast, and hues of a video, as well as produce visual artifacts. Their presentation is also highly dependent upon the kind and configuration of the display on which they're viewed. 

The most fundamental aspect of colour in video is the bit depth. Essentially, a higher bit depth means that there are more available distinct colours, at the cost of a larger file. 

## Containers 

Each file type for video, such as .mp4 or .mkv, represents a container for video and audio, plus additional optional features. Both video and audio streams are encoded using a "codec", which defines how the data is stored on disk, with a trade off between quality and file size. 

MP4 (MPEG-4 Part XIV) is a partially open container format. It's defined by an ISO standard, but there are some patents related to it. It has limited support for subtitles, chapters, and multiple audio tracks. It's great for compatibility as it's supported by the majority of platforms. 

MVK (Matroska Video) is a fully open container standard with very high flexibility. It has excellent support for subtitles, multiple audio tracks, and chapters. 

AVI is a proprietary container format designed by Microsoft. These days, it's considered legacy, with very limited support for subtitling and multiple audio tracks, and no support for chapters. 

MOV is Apple's proprietary container format. It has great support for subtitles, multiple audio tracks, and chapters, and is often used by video editing professionals. 

WebM is an emerging and fully open container standard developed by Google. It has good support for subtitles and multiple audio tracks, but limited support for chapters. 

## Video codecs 

The video codec defines how a video is stored as data. Storing each frame as an individual image would be terribly inefficient, so codecs employ various strategies to make storage more efficient, at the cost of some quality loss. 

Many DVDs and other older media are encoded with the patented MPEG-2 codec, which is widely supported for playback but terribly inefficient and yields low quality results in comparison with modern alternatives. 

H.264 (AVC, Advanced Video Codec) is widely supported for playback, but subject to many patents. 

H.265 (HEVC, Highly Efficient Video Codec) is an improvement upon AVC with higher quality and compression efficiency, though it's also subject to many patents. 

VP9 (Video Processing 9) is an open standard with similarly high compression efficiency and quality, optimised for video streaming. 

AV1 (AOMedia Video 1) is an open standard that provides the best compression ratio and quality. It's compatible with relatively few devices, but support continues to grow. 

## Audio Codecs 

Audio codecs, similar to video codecs, define how audio data is stored as bytes. Unlike video codecs, audio codecs can (but don't always) retain the full quality of the original audio. 

MP3 (MPEG-1 Audio Layer III) is a low-efficiency lossy audio codec with an expired patent. It's supported nearly everywhere, but delivers relatively terrible quality. 

AAC (Advanced Audio Coding) is a slight improvement upon MP3. It remains lossy, but has a higher quality and efficiency, though it is subject to patents. 

Opus is a high-quality lossy codec with an open standard. Its main benefit is its low latency, which makes it better suited for real-time voice communications than media playback. 

FLAC (Free Lossless Audio Codec) is a lossless, high-quality, high-efficiency codec with an open standard. It's the option for retaining full quality in audio. Apple has a variant, ALAC (Apple Lossles Audio Codec), used in their own ecosystem. 

## Container codec support comparison

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
 
 ## Conclusion 

 Picking the best resolution, colour space, codecs, and containers for a video really depends on the data you already have and how much you value quality over file size. 

 There's a lot that hasn't been mentioned here too, including suitability for streaming, support for digital rights management (DRM), error resilience, and so, so much about colours. 
