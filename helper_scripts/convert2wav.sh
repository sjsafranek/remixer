#!/bin/bash

set +e
set +x

IN_FILE=$1

filename=$(basename -- "$IN_FILE")
extension="${filename##*.}"
filename="${filename%.*}"

echo "name: $filename"
echo "type: $extension"

ffmpeg -i "$IN_FILE" "$filename.wav"
