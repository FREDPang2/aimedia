"""
视频合成服务 - Video Compose Service
使用 FFmpeg 合成最终视频：视频片段 + 配音 + 字幕 → 最终成片
支持字幕烧录、背景音乐混入
"""
import os
import subprocess
from typing import Optional


def get_ffmpeg_binary() -> str:
    """获取 FFmpeg 可执行文件路径"""
    return os.environ.get("IMAGEIO_FFMPEG_EXE") or "ffmpeg"


def run_ffmpeg(command: list) -> tuple[bool, str]:
    """
    执行 FFmpeg 命令

    Returns:
        (success, error_message)
    """
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            error_msg = (result.stderr or result.stdout or "").strip()
            return False, error_msg or "ffmpeg failed with no output"
        return True, ""
    except FileNotFoundError:
        return False, "ffmpeg not found"
    except Exception as e:
        return False, str(e)


def compose_video(
    video_path: str,
    audio_path: str,
    subtitle_path: Optional[str],
    output_path: str,
    bgm_path: Optional[str] = None,
    bgm_volume: float = 0.3,
    voice_volume: float = 1.0,
) -> tuple[bool, str]:
    """
    使用 FFmpeg 合成最终视频

    Args:
        video_path: 视频片段路径（无音频）
        audio_path: 配音/旁白音频路径
        subtitle_path: 字幕文件路径（可选，SRT/ASS 格式）
        output_path: 输出视频路径
        bgm_path: 背景音乐路径（可选）
        bgm_volume: 背景音乐音量（0.0-1.0），默认 0.3
        voice_volume: 配音音量（0.0-1.0），默认 1.0

    Returns:
        (success, message)
    """
    ffmpeg = get_ffmpeg_binary()

    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # 检查视频文件
    if not os.path.exists(video_path):
        return False, f"视频文件不存在: {video_path}"
    if not os.path.exists(audio_path):
        return False, f"音频文件不存在: {audio_path}"

    # 构建 FFmpeg 滤镜链
    # 1. 视频：直接使用
    # 2. 配音：设置音量
    # 3. 字幕：烧录到视频
    # 4. BGM：混入

    filter_parts = []
    audio_mix_inputs = []
    audio_map = []

    # 字幕烧录
    if subtitle_path and os.path.exists(subtitle_path):
        subtitle_ext = os.path.splitext(subtitle_path)[1].lower()
        if subtitle_ext == ".ass":
            filter_parts.append(f"ass='{subtitle_path}'")
        elif subtitle_ext == ".srt":
            filter_parts.append(f"subtitles='{subtitle_path}'")
        else:
            return False, f"不支持的字幕格式: {subtitle_ext}，支持 SRT 和 ASS"

    # 构建命令
    cmd = [
        ffmpeg,
        "-y",  # 覆盖输出
        "-i", video_path,  # 输入视频
    ]

    # 配音音轨
    voice_vol_filter = f"volume=enable='between(t,0,{voice_volume * 100})':volume={voice_volume}"
    cmd.extend(["-i", audio_path])  # 输入配音

    # BGM 音轨（可选）
    if bgm_path and os.path.exists(bgm_path):
        cmd.extend(["-i", bgm_path])  # 输入 BGM

    # 音频混合
    if bgm_path and os.path.exists(bgm_path):
        # 配音 + BGM 混合
        # [1:a] 配音音轨 volume -> [2:a] BGM 音量 -> amix 混合
        filter_parts.append(
            f"[1:a]volume={voice_volume}[voice];"
            f"[2:a]volume={bgm_volume}[bgm];"
            f"[voice][bgm]amix=inputs=2:duration=longest[aout]"
        )
        audio_map = ["-map", "0:v", "-map", "[aout]"]
    else:
        # 只有配音
        filter_parts.append(f"[1:a]volume={voice_volume}[aout]")
        audio_map = ["-map", "0:v", "-map", "[aout]"]

    # 应用视频滤镜（字幕）
    if filter_parts:
        video_filter = ",".join(filter_parts)
        cmd.extend(["-vf", video_filter])

    # 音频映射
    cmd.extend(audio_map)

    # 编码参数
    cmd.extend([
        "-c:v", "libx264",  # H.264 视频编码
        "-preset", "medium",
        "-crf", "23",
        "-c:a", "aac",  # AAC 音频编码
        "-b:a", "192k",
        "-shortest",  # 以最短音轨结束
        output_path,
    ])

    success, error = run_ffmpeg(cmd)
    if not success:
        return False, f"FFmpeg 合成失败: {error}"

    if not os.path.exists(output_path):
        return False, "输出文件未生成"

    return True, output_path


def compose_video_simple(
    video_path: str,
    audio_path: str,
    output_path: str,
) -> tuple[bool, str]:
    """
    简单合成：视频 + 配音（无字幕、无 BGM）

    Args:
        video_path: 视频片段路径
        audio_path: 配音音频路径
        output_path: 输出视频路径

    Returns:
        (success, message)
    """
    return compose_video(
        video_path=video_path,
        audio_path=audio_path,
        subtitle_path=None,
        output_path=output_path,
    )


if __name__ == "__main__":
    # 简单测试
    import tempfile

    test_video = "/tmp/test_video.mp4"
    test_audio = "/tmp/test_audio.mp3"
    test_output = "/tmp/test_output.mp4"

    # 创建空白测试文件（实际使用时请替换为真实文件）
    import os
    if os.path.exists(test_video) and os.path.exists(test_audio):
        success, msg = compose_video_simple(test_video, test_audio, test_output)
        print(f"合成结果: {success}, {msg}")
    else:
        print("测试文件不存在，跳过测试")
