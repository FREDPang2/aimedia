"""
视频合成服务 - Video Compose Service
使用 FFmpeg 合成最终视频：视频片段 + 配音 + 字幕 → 最终成片
支持字幕烧录、背景音乐混入

FFmpeg 需要提前安装:
  - Linux/WSL: sudo apt install ffmpeg
  - 或 pip install imageio-ffmpeg (自带 ffmpeg 二进制)
"""
import os
import subprocess
from typing import Optional


def get_ffmpeg_binary() -> str:
    """获取 FFmpeg 可执行文件路径"""
    return os.environ.get("IMAGEIO_FFMPEG_EXE") or os.environ.get("FFMPEG_BINARY") or "ffmpeg"


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
        return False, "ffmpeg not found in PATH"
    except Exception as e:
        return False, str(e)


def check_ffmpeg() -> tuple[bool, str]:
    """检查 FFmpeg 是否可用"""
    ffmpeg = get_ffmpeg_binary()
    try:
        result = subprocess.run(
            [ffmpeg, "-version"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            version_line = result.stdout.split("\n")[0]
            return True, version_line
        return False, "ffmpeg check failed"
    except FileNotFoundError:
        return False, f"{ffmpeg} not found in PATH"


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

    # 检查输入文件
    if not os.path.exists(video_path):
        return False, f"视频文件不存在: {video_path}"
    if not os.path.exists(audio_path):
        return False, f"音频文件不存在: {audio_path}"

    # 构建命令
    cmd = [
        ffmpeg,
        "-y",  # 覆盖输出
        "-i", video_path,  # 输入0: 视频
        "-i", audio_path,  # 输入1: 配音
    ]

    # 构建滤镜链
    filter_parts = []
    audio_filter = ""
    subtitle_filter = ""

    # 字幕烧录
    if subtitle_path and os.path.exists(subtitle_path):
        subtitle_ext = os.path.splitext(subtitle_path)[1].lower()
        if subtitle_ext == ".ass":
            subtitle_filter = f"ass='{subtitle_path}'"
        elif subtitle_ext == ".srt":
            subtitle_filter = f"subtitles='{subtitle_path}'"
        else:
            return False, f"不支持的字幕格式: {subtitle_ext}，支持 SRT 和 ASS"

    # 音频混合
    if bgm_path and os.path.exists(bgm_path):
        cmd.append("-i")  # 输入2: BGM
        # 配音音量 + BGM 混合
        # [1:a] 配音 volume → [2:a] BGM volume → amix
        audio_filter = (
            f"[1:a]volume={voice_volume}[voice];"
            f"[2:a]volume={bgm_volume}[bgm];"
            f"[voice][bgm]amix=inputs=2:duration=longest[aout]"
        )
    else:
        # 只有配音
        audio_filter = f"[1:a]volume={voice_volume}[aout]"

    # 组装完整滤镜
    if subtitle_filter and audio_filter:
        filter_parts.append(subtitle_filter)
        filter_parts.append(audio_filter)
        video_filter = ";".join(filter_parts)
    elif subtitle_filter:
        video_filter = subtitle_filter
    elif audio_filter:
        video_filter = audio_filter
    else:
        video_filter = None

    if video_filter:
        cmd.extend(["-filter_complex", video_filter])
        cmd.extend(["-map", "0:v", "-map", "[aout]"])
    else:
        cmd.extend(["-map", "0:v", "-map", "1:a"])

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


def concatenate_videos(
    video_paths: list,
    output_path: str,
) -> tuple[bool, str]:
    """
    将多个视频片段拼接成一个视频（无音频处理）

    使用 FFmpeg concat demuxer，需要视频编码格式一致。

    Args:
        video_paths: 视频片段路径列表
        output_path: 输出视频路径

    Returns:
        (success, message)
    """
    if not video_paths:
        return False, "没有输入视频"
    if len(video_paths) == 1:
        # 只有一个视频，直接复制
        import shutil
        shutil.copy(video_paths[0], output_path)
        return True, output_path

    ffmpeg = get_ffmpeg_binary()
    output_dir = os.path.dirname(output_path) or "."
    os.makedirs(output_dir, exist_ok=True)

    # 创建 concat 文件
    concat_file = os.path.join(output_dir, "concat_list.txt")
    with open(concat_file, "w", encoding="utf-8") as f:
        for path in video_paths:
            if not os.path.exists(path):
                return False, f"视频文件不存在: {path}"
            # 转义路径中的单引号
            escaped = path.replace("'", "'\\''")
            f.write(f"file '{escaped}'\n")

    cmd = [
        ffmpeg,
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_file,
        "-c", "copy",  # 直接复制，不重新编码
        output_path,
    ]

    success, error = run_ffmpeg(cmd)
    os.remove(concat_file)

    if not success:
        return False, f"视频拼接失败: {error}"
    if not os.path.exists(output_path):
        return False, "输出文件未生成"

    return True, output_path


def concatenate_with_audio(
    video_paths: list,
    audio_path: str,
    output_path: str,
) -> tuple[bool, str]:
    """
    拼接多个视频片段并混入配音音频

    Args:
        video_paths: 视频片段路径列表
        audio_path: 配音音频路径
        output_path: 输出视频路径

    Returns:
        (success, message)
    """
    # 先拼接视频
    temp_video = output_path + ".concat.mp4"
    ok, msg = concatenate_videos(video_paths, temp_video)
    if not ok:
        return False, f"视频拼接失败: {msg}"

    # 再合成音频
    ok, msg = compose_video_simple(temp_video, audio_path, output_path)
    os.remove(temp_video)
    return ok, msg


if __name__ == "__main__":
    import tempfile
    import shutil

    # 检查 FFmpeg
    ok, msg = check_ffmpeg()
    print(f"FFmpeg 状态: {'✓' if ok else '✗'} {msg}")

    test_video = "/tmp/test_video.mp4"
    test_audio = "/tmp/test_audio.mp3"
    test_output = "/tmp/test_output.mp4"

    if os.path.exists(test_video) and os.path.exists(test_audio):
        success, msg = compose_video_simple(test_video, test_audio, test_output)
        print(f"合成结果: {'✓' if success else '✗'} {msg}")
    else:
        print("测试文件不存在，跳过合成测试")
