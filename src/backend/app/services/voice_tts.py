"""
MiniMax TTS Service - 语音合成服务
使用 MiniMax API 将文本转换为语音
"""
import os
import requests

# MiniMax TTS API 配置
MINIMAX_API_KEY = "sk-cp-IP7k8Y38aSLksx9QKZDZTPO9nR1_rjlnzuiok7Oy1Gss0BWbkaitqD2DH0ZTJ_99j0rsJ9Y80uqe15bg8gWXQI0EqFQdI_R4b5U2XrG-5PALXstS4EVETkw"
MINIMAX_BASE_URL = "https://api.minimaxi.com"

# 默认中文语音
DEFAULT_VOICE = "longxiao"


def generate_voice(text: str, output_path: str, voice: str = DEFAULT_VOICE) -> bool:
    """
    使用 MiniMax TTS API 生成语音

    Args:
        text: 要转换为语音的文本
        output_path: 输出的音频文件路径（支持 .mp3 格式）
        voice: 语音名称，默认使用中文男声 "longxiao"

    Returns:
        bool: 生成成功返回 True，失败返回 False
    """
    text = text.strip()
    if not text:
        return False

    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    url = f"{MINIMAX_BASE_URL}/v1/t2a_v2"

    payload = {
        "model": "speech-02-hd",
        "text": text,
        "stream": False,
        "voice_setting": {
            "voice_id": voice,
        },
        "audio_setting": {
            "sample_rate": 32000,
            "format": "mp3",
            "bitrate": 128000,
        },
    }

    headers = {
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json",
    }

    for attempt in range(3):
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                return True
            else:
                print(f"[voice_tts] attempt {attempt + 1} failed: {response.status_code} {response.text[:200]}")
        except Exception as e:
            print(f"[voice_tts] attempt {attempt + 1} exception: {e}")

    return False


if __name__ == "__main__":
    # 简单测试
    test_text = "你好，欢迎使用 MiniMax 语音合成服务。"
    test_output = "/tmp/test_voice.mp3"
    success = generate_voice(test_text, test_output)
    print(f"生成成功: {success}" if success else "生成失败")
