#!/usr/bin/env python3.12
import asyncio
import edge_tts
import os
import json
import sys

VOICES = {
    "🎀 晓晓（女，温柔）": "zh-CN-XiaoxiaoNeural",
    "🎙️ 云扬（男，专业）": "zh-CN-YunyangNeural",
    "✨ 晓伊（女，活泼）": "zh-CN-XiaoyiNeural",
    "🌟 云夏（男，年轻）": "zh-CN-YunxiaNeural",
    "💫 云希（男，阳光）": "zh-CN-YunxiNeural",
    "🔥 云建（男，磁性）": "zh-CN-YunjianNeural",
    "🧧 东北话·小北（女）": "zh-CN-liaoning-XiaobeiNeural",
    "🌶 陕西话·小妮（女）": "zh-CN-shaanxi-XiaoniNeural",
    "🥮 粤语·晓佳（女）": "zh-HK-HiuGaaiNeural",
    "🍵 粤语·晓曼（女）": "zh-HK-HiuMaanNeural",
    "🎋 粤语·云龙（男）": "zh-HK-WanLungNeural",
    "🌸 台湾·小晨（女）": "zh-TW-HsiaoChenNeural",
    "🎍 台湾·允泽（男）": "zh-TW-YunJheNeural",
    "🫧 台湾·小玉（女）": "zh-TW-HsiaoYuNeural",
    "🇺🇸 英语·Jenny（女）": "en-US-JennyNeural",
    "🇺🇸 英语·Guy（男）": "en-US-GuyNeural",
    "🇬🇧 英语·Sonia（女）": "en-GB-SoniaNeural",
    "🇯🇵 日语·Nanami（女）": "ja-JP-NanamiNeural",
    "🇯🇵 日语·Keita（男）": "ja-JP-KeitaNeural",
    "🇰🇷 韩语·SunHi（女）": "ko-KR-SunHiNeural",
    "🇰🇷 韩语·InJoon（男）": "ko-KR-InJoonNeural"
}

async def generate(text: str, voice: str = "zh-CN-XiaoxiaoNeural", output_path: str = "/tmp/output_tts.mp3") -> dict:
    try:
        tts = edge_tts.Communicate(text=text, voice=voice)
        await tts.save(output_path)
        size = os.path.getsize(output_path)
        return {"success": True, "path": output_path, "size": size, "voice": voice}
    except Exception as e:
        return {"success": False, "error": str(e)}

def run(text: str, voice_name: str = "🎀 晓晓（女，温柔）", output_path: str = "/tmp/output_tts.mp3") -> dict:
    voice = VOICES.get(voice_name, "zh-CN-XiaoxiaoNeural")
    return asyncio.run(generate(text, voice, output_path))

if __name__ == "__main__":
    text = sys.argv[1] if len(sys.argv) > 1 else "测试语音"
    result = run(text)
    print(json.dumps(result, ensure_ascii=False, indent=2))
