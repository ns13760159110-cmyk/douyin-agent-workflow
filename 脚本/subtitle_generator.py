#!/usr/bin/env python3.12
import sys
import os
import json
import subprocess
import whisper

def extract_audio(video_path: str, audio_path: str) -> bool:
    cmd = [
        "ffmpeg", "-i", video_path,
        "-vn", "-acodec", "mp3",
        "-ar", "16000", "-ac", "1",
        audio_path, "-y"
    ]
    result = subprocess.run(cmd, capture_output=True)
    return result.returncode == 0

def generate_subtitles(audio_path: str, model_size: str = "base") -> dict:
    model = whisper.load_model(model_size)
    result = model.transcribe(audio_path, language="zh", word_timestamps=True)
    segments = []
    for seg in result["segments"]:
        segments.append({
            "start": round(seg["start"], 2),
            "end": round(seg["end"], 2),
            "text": seg["text"].strip()
        })
    return {
        "text": result["text"].strip(),
        "segments": segments
    }

def generate_srt(segments: list) -> str:
    srt = ""
    for i, seg in enumerate(segments, 1):
        start = format_time(seg["start"])
        end = format_time(seg["end"])
        srt += f"{i}\n{start} --> {end}\n{seg['text']}\n\n"
    return srt

def format_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def burn_subtitles(video_path: str, srt_path: str, output_path: str) -> bool:
    cmd = [
        "ffmpeg", "-i", video_path,
        "-vf", f"subtitles={srt_path}:force_style='FontSize=18,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,Outline=1'",
        "-c:a", "copy",
        output_path, "-y"
    ]
    result = subprocess.run(cmd, capture_output=True)
    return result.returncode == 0

def process(video_path: str, output_dir: str = "/tmp") -> dict:
    base = os.path.splitext(os.path.basename(video_path))[0]
    audio_path = f"{output_dir}/{base}.mp3"
    srt_path = f"{output_dir}/{base}.srt"
    output_path = f"{output_dir}/{base}_subtitled.mp4"

    # 提取音频
    if not extract_audio(video_path, audio_path):
        return {"success": False, "error": "音频提取失败"}

    # 生成字幕
    result = generate_subtitles(audio_path)

    # 写入SRT文件
    srt_content = generate_srt(result["segments"])
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt_content)

    # 烧录字幕到视频
    burn_subtitles(video_path, srt_path, output_path)

    return {
        "success": True,
        "text": result["text"],
        "segments": result["segments"],
        "srt_path": srt_path,
        "output_path": output_path if os.path.exists(output_path) else None
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "请提供视频路径"}, ensure_ascii=False))
        sys.exit(1)
    result = process(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))
