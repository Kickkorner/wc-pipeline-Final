#!/usr/bin/env bash
set -e
WORK=work
ASSETS=assets
mkdir -p "$WORK"

CINEMATIC_FILTER="eq=contrast=1.08:saturation=1.2:gamma=0.95,vignette"

# 4K base resolution
BASE_W=3840
BASE_H=2160

SEGMENTS=()
for f in "$WORK"/scene_*.png; do
    idx=$(basename "$f" .png | sed 's/scene_//')
    out="$WORK/seg_${idx}.mp4"
    ffmpeg -y -loop 1 -i "$f" -t 5 \
        -vf "scale=4800:2700,zoompan=z='min(zoom+0.0015,1.15)':d=125:s=${BASE_W}x${BASE_H},${CINEMATIC_FILTER}" \
        -c:v libx264 -pix_fmt yuv420p "$out"
    SEGMENTS+=("$out")
done

if [ ${#SEGMENTS[@]} -eq 1 ]; then
    cp "${SEGMENTS[0]}" "$WORK/base.mp4"
else
    INPUTS=()
    for s in "${SEGMENTS[@]}"; do INPUTS+=(-i "$s"); done

    FILTER=""
    PREV="0:v"
    DUR=5
    OFFSET=0
    for i in "${!SEGMENTS[@]}"; do
        if [ "$i" -eq 0 ]; then continue; fi
        OFFSET=$((DUR * i - 1))
        CUR="${i}:v"
        OUT="v${i}"
        FILTER+="[$PREV][$CUR]xfade=transition=fade:duration=1:offset=${OFFSET}[$OUT];"
        PREV="$OUT"
    done
    FILTER="${FILTER%;}"

    ffmpeg -y "${INPUTS[@]}" -filter_complex "$FILTER" -map "[$PREV]" \
        -c:v libx264 -pix_fmt yuv420p "$WORK/base.mp4"
fi

DURATION=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$WORK/base.mp4")

if [ -f "$ASSETS/music.mp3" ]; then
    ffmpeg -y -i "$WORK/base.mp4" -stream_loop -1 -i "$ASSETS/music.mp3" \
        -filter_complex "[1:a]atrim=0:${DURATION},afade=t=in:d=2,afade=t=out:st=$(echo "$DURATION-2" | bc):d=2[a]" \
        -map 0:v -map "[a]" -c:v copy -shortest "$WORK/base_audio.mp4"
else
    cp "$WORK/base.mp4" "$WORK/base_audio.mp4"
fi

# Shorts: 4K vertical (2160x3840)
ffmpeg -y -i "$WORK/base_audio.mp4" -t 59 \
    -vf "scale=2160:3840:force_original_aspect_ratio=increase,crop=2160:3840" \
    -c:v libx264 -preset slow -crf 18 -c:a aac "$WORK/short.mp4"

# Long-form: 4K horizontal (3840x2160)
ffmpeg -y -stream_loop 15 -i "$WORK/base_audio.mp4" -t 300 \
    -c:v libx264 -preset slow -crf 18 -c:a aac "$WORK/long.mp4"

echo "Edit complete: work/short.mp4 and work/long.mp4 ready (4K)."
