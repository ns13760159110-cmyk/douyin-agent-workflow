#!/usr/bin/env python3.12
"""一键成片：从抖音链接到成品视频的全流程"""
import os
import sys
import json
import subprocess
import requests
import time

sys.path.insert(0, os.path.dirname(__file__))
import douyin_api
import subtitle_generator
import cover_extractor
import tts_generator
import bgm_mixer

OUTPUT_DIR = "/tmp/auto_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Dify配置
DIFY_API_URL = "http://localhost/v1/workflows/run"
REWRITE_KEY = "app-WawEE5glIGCLTFK52H3WJDn7"


def step(name, callback, *args, **kwargs):
    """执行一步并打印进度"""
    print(f"⏳ {name}...")
    start = time.time()
    try:
        result = callback(*args, **kwargs)
        elapsed = round(time.time() - start, 1)
        print(f"✅ {name} 完成 ({elapsed}s)")
        return {"success": True, "data": result, "elapsed": elapsed}
    except Exception as e:
        print(f"❌ {name} 失败: {e}")
        return {"success": False, "error": str(e)}


def download_video(url, save_path):
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
        "Referer": "https://www.douyin.com/",
    }
    r = requests.get(url, headers=headers, timeout=120, stream=True)
    r.raise_for_status()
    with open(save_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
    return save_path


def rewrite_text(text):
    res = requests.post(
        DIFY_API_URL,
        headers={"Authorization": f"Bearer {REWRITE_KEY}", "Content-Type": "application/json"},
        json={"inputs": {"original_text": text}, "response_mode": "blocking", "user": "auto"},
        timeout=60,
    )
    return res.json()["data"]["outputs"].get("new_text", "")


def combine_video(video_path, audio_path, output_path, duration=None):
    """用原视频画面+新音频合成视频，压缩适配手机播放"""
    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-i", audio_path,
        "-map", "0:v",
        "-map", "1:a",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "28",
        "-vf", "scale=720:-2",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        "-movflags", "+faststart",
        output_path, "-y",
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return output_path


def burn_subtitles(video_path, srt_path, output_path):
    subtitle_generator.burn_subtitles(video_path, srt_path, output_path)
    return output_path


def run_pipeline(
    url: str,
    voice_name: str = "晓晓（女，温柔）",
    bgm_name: str = None,
    bgm_vol: float = 0.15,
) -> dict:
    """一键成片主流程"""
    task_id = str(int(time.time()))
    work_dir = f"{OUTPUT_DIR}/{task_id}"
    os.makedirs(work_dir, exist_ok=True)

    results = {"task_id": task_id, "steps": [], "outputs": {}}

    # 1. 解析视频
    def do_parse():
        result = douyin_api.parse(url)
        if not result.get("success"):
            raise Exception(result.get("error", "解析失败"))
        return result

    r = step("解析视频", do_parse)
    results["steps"].append({"name": "解析视频", **r})
    if not r["success"]:
        return results
    video_info = r["data"]
    results["outputs"]["title"] = video_info.get("desc", "")
    results["outputs"]["author"] = video_info.get("author", "")

    # 2. 下载视频
    video_path = f"{work_dir}/original.mp4"
    r = step("下载视频", lambda: download_video(video_info["video_url"], video_path))
    results["steps"].append({"name": "下载视频", **r})
    if not r["success"]:
        return results

    # 3. 生成字幕（提取原文案）
    r = step("提取原文案", lambda: subtitle_generator.process(video_path, work_dir))
    results["steps"].append({"name": "提取原文案", **r})
    if not r["success"]:
        return results
    original_text = r["data"]["text"]
    srt_path = r["data"]["srt_path"]
    results["outputs"]["original_text"] = original_text

    # 4. AI改写文案
    r = step("AI改写文案", lambda: rewrite_text(original_text))
    results["steps"].append({"name": "AI改写文案", **r})
    if not r["success"]:
        return results
    new_text = r["data"]
    results["outputs"]["new_text"] = new_text

    # 5. TTS生成音频
    audio_path = f"{work_dir}/voice.mp3"
    r = step("生成新音频", lambda: tts_generator.run(new_text, voice_name, audio_path))
    results["steps"].append({"name": "生成新音频", **r})
    if not r["success"]:
        return results

    # 6. BGM混音（可选）
    final_audio = audio_path
    if bgm_name:
        bgm_list = bgm_mixer.list_bgm()
        bgm = next((b for b in bgm_list if b["name"] == bgm_name), None)
        if bgm:
            mixed_path = f"{work_dir}/voice_bgm.mp3"
            r = step(
                "混合BGM",
                lambda: bgm_mixer.mix_audio(audio_path, bgm["path"], mixed_path, bgm_vol=bgm_vol),
            )
            results["steps"].append({"name": "混合BGM", **r})
            if r["success"]:
                final_audio = mixed_path

    # 7. 提取封面
    r = step("提取封面", lambda: cover_extractor.extract_cover(video_path, work_dir, count=1))
    results["steps"].append({"name": "提取封面", **r})
    if not r["success"]:
        return results
    cover_path = r["data"]["covers"][0]["path"]
    results["outputs"]["cover_path"] = cover_path

    # 8. 合成最终视频
    final_video = f"{work_dir}/final.mp4"
    r = step("合成最终视频", lambda: combine_video(video_path, final_audio, final_video))
    results["steps"].append({"name": "合成最终视频", **r})
    if not r["success"]:
        return results

    results["outputs"]["final_video"] = final_video
    results["success"] = True
    return results


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://v.douyin.com/-bi-Cpv7koM/"
    voice = sys.argv[2] if len(sys.argv) > 2 else "晓晓（女，温柔）"
    bgm = sys.argv[3] if len(sys.argv) > 3 else "轻快活泼"
    result = run_pipeline(url, voice, bgm)
    print("\n" + "=" * 50)
    print(json.dumps({k: v for k, v in result.items() if k != "steps"}, ensure_ascii=False, indent=2))
