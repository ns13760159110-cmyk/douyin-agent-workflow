#!/usr/bin/env python3.12
import subprocess
import os
import json
import sys

BGM_DIR = os.path.join(os.path.dirname(__file__), "bgm")

def list_bgm() -> list:
    files = []
    for f in os.listdir(BGM_DIR):
        if f.endswith(('.mp3', '.wav', '.m4a')):
            files.append({
                "name": os.path.splitext(f)[0],
                "path": os.path.join(BGM_DIR, f),
                "filename": f
            })
    return files

def mix_audio(voice_path: str, bgm_path: str, output_path: str,
              voice_vol: float = 1.0, bgm_vol: float = 0.1) -> dict:
    """人声+BGM混音"""
    try:
        cmd = [
            "ffmpeg",
            "-i", voice_path,
            "-i", bgm_path,
            "-filter_complex",
            f"[0:a]volume={voice_vol}[v];[1:a]volume={bgm_vol}[b];[v][b]amix=inputs=2:duration=first:dropout_transition=2[out]",
            "-map", "[out]",
            "-c:a", "mp3",
            output_path, "-y"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return {"success": True, "path": output_path}
        else:
            return {"success": False, "error": result.stderr[-200:]}
    except Exception as e:
        return {"success": False, "error": str(e)}

def mix_video_bgm(video_path: str, bgm_path: str, output_path: str,
                  bgm_vol: float = 0.1) -> dict:
    """给视频加BGM（保留原声）"""
    try:
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-i", bgm_path,
            "-filter_complex",
            f"[0:a]volume=1.0[v];[1:a]volume={bgm_vol}[b];[v][b]amix=inputs=2:duration=first[out]",
            "-map", "0:v",
            "-map", "[out]",
            "-c:v", "copy",
            "-c:a", "mp3",
            output_path, "-y"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return {"success": True, "path": output_path}
        else:
            return {"success": False, "error": result.stderr[-200:]}
    except Exception as e:
        return {"success": False, "error": str(e)}

def download_free_bgm():
    """下载几首免费BGM"""
    bgm_list = [
        {"name": "轻快活泼", "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"},
        {"name": "温柔舒缓", "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3"},
        {"name": "激情澎湃", "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3"}
    ]
    for bgm in bgm_list:
        output = os.path.join(BGM_DIR, f"{bgm['name']}.mp3")
        if not os.path.exists(output):
            cmd = ["wget", "-q", "-O", output, bgm["url"]]
            result = subprocess.run(cmd, capture_output=True)
            if result.returncode == 0:
                print(f"下载成功：{bgm['name']}")
            else:
                print(f"下载失败：{bgm['name']}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "download":
        download_free_bgm()
        print(json.dumps(list_bgm(), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(list_bgm(), ensure_ascii=False, indent=2))
