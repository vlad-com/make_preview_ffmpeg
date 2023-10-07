# make_preview_ffmpeg
Python script to easily make a video preview with ffmpeg

## Easy example for CUDA videocard:
```bash
python3 make_preview.py -f input.mp4 -hw cuda
```
## More complicated example using QSV videocard(Intel) to get HEVC video with IOS support divided into 10 parts of 1 second
```bash
python3 make_preview.py -f input.mp4 -hw qsv -c hevc -s 10 -p 1
```
## Options:
```bash
  -h, --help                     | show this help message and exit
  -f FILE, --file FILE           | Path to file
  -hw HWACCEL, --hwaccel HWACCEL | Hardware acceleration (can be: [qsv, cuda])
  -c CODEC, --codec CODEC        | Codec (default: h264)
  -a AUDIO, --audio AUDIO        | Turn on/off audio (default: True)
  -s SPLIT, --split SPLIT        | Split by parts (default: 12)
  -p PART, --part PART           | Part duration in seconds (default: 0.766)
  -q QUALITY, --quality QUALITY  | Video quality scale is 0–51, where 0 is lossless, 51 is worst quality possible (default: 23)
  -o OUTPUT, --output OUTPUT     | Show Output
```
