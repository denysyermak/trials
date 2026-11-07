#!/bin/bash
# encode.sh <input.mov> <subs.ass> <out.mp4>
set -e
ffmpeg -y -loglevel error -i "$1" \
  -vf "scale=1080:1920:flags=lanczos,fps=30,ass=$2" \
  -c:v libx264 -preset veryfast -crf 21 -maxrate 8M -bufsize 16M -pix_fmt yuv420p -profile:v high \
  -c:a aac -b:a 128k -ar 48000 -movflags +faststart "$3"
