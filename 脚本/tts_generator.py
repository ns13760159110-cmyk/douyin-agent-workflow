#!/usr/bin/env python3.12
import asyncio
import edge_tts
import os
import json
import sys

VOICES = {
    "晓晓（女，温柔）": "zh-CN-XiaoxiaoNeural",
    "晓伊（女，活泼）": "zh-CN-XiaoyiNeural",
    "云扬（男，专业）": "zh-CN-YunyangNeural",
    "云夏（男，年轻）": "zh-CN-YunxiaNeural",
    "云希（男，阳光）": "zh-CN-YunxiNeural",
    "云健（男，沉稳）": "zh-CN-YunjianNeural",
    "晓北（女，东北）": "zh-CN-liaoning-XiaobeiNeural",
    "晓妮（女，陕西）": "zh-CN-shaanxi-XiaoniNeural",
}

async def generate(text: str, voice: str = "zh-CN-XiaoxiaoNeural", output_path: str = "/tmp/output_tts.mp3") -> dict:
    try:
        tts = edge_tts.Communicate(text=text, voice=voice)
        await tts.save(output_path)
        size = os.path.getsize(output_path)
        return {"success": True, "path": output_path, "size": size, "voice": voice}
    except Exception as e:
        return {"success": False, "error": str(e)}

def run(text: str, voice_name: str = "晓晓（女，温柔）", output_path: str = "/tmp/output_tts.mp3") -> dict:
    voice = VOICES.get(voice_name, "zh-CN-XiaoxiaoNeural")
    return asyncio.run(generate(text, voice, output_path))

if __name__ == "__main__":
    text = sys.argv[1] if len(sys.argv) > 1 else "测试语音"
    result = run(text)
    print(json.dumps(result, ensure_ascii=False, indent=2))
