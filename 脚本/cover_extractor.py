#!/usr/bin/env python3.12
import sys
import os
import json
import subprocess

def extract_cover(video_path: str, output_dir: str = "/tmp", count: int = 3) -> dict:
    """
    从视频提取封面
    count: 提取几张候选封面
    """
    base = os.path.splitext(os.path.basename(video_path))[0]

    # 获取视频时长
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    info = json.loads(result.stdout)
    duration = float(info["format"]["duration"])

    covers = []
    # 在视频1/4、1/2、3/4处各截一张
    positions = [duration * i / (count + 1) for i in range(1, count + 1)]
    for i, pos in enumerate(positions):
        cover_path = f"{output_dir}/{base}_cover_{i+1}.jpg"
        cmd = [
            "ffmpeg", "-i", video_path,
            "-ss", str(pos),
            "-vframes", "1",
            "-vf", "scale=720:-1",
            "-q:v", "2",
            cover_path, "-y"
        ]
        subprocess.run(cmd, capture_output=True)
        if os.path.exists(cover_path):
            covers.append({
                "index": i + 1,
                "path": cover_path,
                "time": round(pos, 2)
            })

    # 额外提取最清晰帧（I帧）
    best_path = f"{output_dir}/{base}_cover_best.jpg"
    cmd = [
        "ffmpeg", "-i", video_path,
        "-vf", "select=eq(pict_type\\,I),scale=720:-1",
        "-vframes", "1",
        "-q:v", "2",
        best_path, "-y"
    ]
    subprocess.run(cmd, capture_output=True)
    if os.path.exists(best_path):
        covers.insert(0, {
            "index": 0,
            "path": best_path,
            "time": 0,
            "label": "推荐封面"
        })

    return {
        "success": True,
        "duration": round(duration, 2),
        "covers": covers
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "请提供视频路径"}, ensure_ascii=False))
        sys.exit(1)
    result = extract_cover(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))
