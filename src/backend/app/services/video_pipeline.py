"""
视频生成管线 - Video Generation Pipeline
完整流程：脚本解析 → MiniMax TTS → Kling API → FFmpeg 合成

调用顺序:
  1. parse_script()       - 解析脚本 JSON，提取场景列表
  2. generate_voice()      - MiniMax TTS 生成配音
  3. generate_video_clip() - Kling API 生成视频片段
  4. compose_final()       - FFmpeg 合成最终成片

用法:
  result = run_pipeline(episode_id, script_json, output_dir="/tmp/videos")
"""
import json
import os
import time
import uuid
from typing import Optional

# 本地服务
from . import voice_tts
from . import kling
from . import video_compose


# =============================================================================
# 1. 脚本解析
# =============================================================================

def parse_script(script_json: str) -> list[dict]:
    """
    解析脚本 JSON，提取场景列表

    支持两种格式:
    - storyboard 格式: {"scenes": [{"timecode": "00:00-00:05", "character": "...", "action": "...", "dialogue": "..."}]}
    - plain 格式: [{"dialogue": "..."}] 或 [{"text": "..."}]

    Returns:
        场景列表，每个场景是一个 dict，至少包含:
        - text: 用于 TTS 的文本
        - prompt: 用于 Kling 的视频描述（若无则用 text）
        - duration: 预估时长（秒），默认 5s
    """
    try:
        if isinstance(script_json, str):
            data = json.loads(script_json)
        else:
            data = script_json
    except json.JSONDecodeError as e:
        raise ValueError(f"脚本 JSON 解析失败: {e}")

    scenes = []

    # shots 格式: {"shots": [{"shot_id": 1, "narration": "...", "video_prompt": "...", "duration": 5}]}
    if isinstance(data, dict) and "shots" in data:
        for shot in data["shots"]:
            text = shot.get("narration") or shot.get("voiceover_text") or shot.get("text") or ""
            prompt = shot.get("video_prompt") or shot.get("prompt") or text
            duration = shot.get("duration", 5)
            try:
                duration = int(duration)
            except (ValueError, TypeError):
                duration = 5
            scenes.append({
                "index": shot.get("shot_id", 0),
                "text": text,
                "prompt": prompt,
                "duration": duration,
                "character": shot.get("scene") or shot.get("character") or "",
                "timecode": "",
                "camera": shot.get("camera") or "",
                "music": "",
            })

    # storyboard 格式
    elif isinstance(data, dict) and "scenes" in data:
        for i, scene in enumerate(data["scenes"]):
            text = scene.get("dialogue") or scene.get("text") or ""
            prompt = scene.get("action") or scene.get("prompt") or text

            # 解析时长
            timecode = scene.get("timecode", "")
            if timecode and "-" in timecode:
                try:
                    start_str, end_str = timecode.split("-")
                    start_parts = list(map(float, start_str.split(":")))
                    end_parts = list(map(float, end_str.split(":")))
                    start_s = start_parts[0] * 60 + start_parts[1]
                    end_s = end_parts[0] * 60 + end_parts[1]
                    duration = int(end_s - start_s)
                    duration = max(5, min(duration, 10))
                except Exception:
                    duration = 5
            else:
                duration = 5

            scenes.append({
                "index": i,
                "text": text,
                "prompt": prompt,
                "duration": duration,
                "character": scene.get("character", ""),
                "timecode": timecode,
                "camera": scene.get("camera_movement") or scene.get("camera", ""),
                "music": scene.get("music_effects") or "",
            })

    # 纯列表格式: [{"dialogue": "..."}]
    elif isinstance(data, list):
        for i, item in enumerate(data):
            text = item.get("dialogue") or item.get("text") or str(item)
            scenes.append({
                "index": i,
                "text": text,
                "prompt": text,
                "duration": 5,
                "character": item.get("character", ""),
                "timecode": "",
                "camera": "",
                "music": "",
            })

    else:
        raise ValueError(f"未知脚本格式: {type(data)}")

    if not scenes:
        raise ValueError("脚本中没有找到有效场景")

    return scenes


# =============================================================================
# 2. MiniMax TTS - 配音生成
# =============================================================================

def generate_voice_for_scene(
    text: str,
    output_path: str,
    voice: str = "longxiao",
) -> tuple[bool, str]:
    """
    为单个场景生成配音

    Args:
        text: 要转换的文本
        output_path: 音频输出路径
        voice: 语音名称

    Returns:
        (success, message)
    """
    if not text or not text.strip():
        return True, ""  # 空文本不算错误

    ok = voice_tts.generate_voice(text.strip(), output_path, voice=voice)
    if ok:
        return True, output_path
    return False, f"TTS 生成失败"


def generate_all_voices(
    scenes: list[dict],
    output_dir: str,
    voice: str = "longxiao",
) -> tuple[bool, str, list[str]]:
    """
    为所有场景生成配音，返回音频文件列表

    Returns:
        (success, message, audio_paths)
    """
    os.makedirs(output_dir, exist_ok=True)
    audio_paths = []

    for i, scene in enumerate(scenes):
        text = scene["text"]
        audio_path = os.path.join(output_dir, f"voice_{i:03d}.mp3")

        ok, msg = generate_voice_for_scene(text, audio_path, voice=voice)
        if not ok:
            return False, f"场景 {i} 配音失败: {msg}", []
        audio_paths.append(audio_path)
        print(f"  [TTS] 场景 {i}: {text[:30]}... → {audio_path}")

    return True, "", audio_paths


# =============================================================================
# 3. Kling API - 视频片段生成
# =============================================================================

def generate_video_clip(
    prompt: str,
    output_path: str,
    aspect_ratio: str = "16:9",
    duration: int = 5,
    model: str = "c1",
) -> tuple[bool, str]:
    """
    为单个场景生成视频片段

    Args:
        prompt: Kling 视频描述
        output_path: 输出视频路径
        aspect_ratio: 画面比例
        duration: 时长（秒）
        model: Kling 模型

    Returns:
        (success, message)
    """
    ok, msg = kling.generate_video(
        prompt=prompt,
        output_path=output_path,
        aspect_ratio=aspect_ratio,
        duration=duration,
        model=model,
        poll_interval=5.0,
        max_wait=300.0,
    )
    return ok, msg


def generate_all_video_clips(
    scenes: list[dict],
    output_dir: str,
    aspect_ratio: str = "16:9",
    model: str = "c1",
) -> tuple[bool, str, list[str]]:
    """
    为所有场景生成视频片段

    Returns:
        (success, message, video_paths)
    """
    os.makedirs(output_dir, exist_ok=True)
    video_paths = []

    for i, scene in enumerate(scenes):
        prompt = scene["prompt"]
        duration = scene.get("duration", 5)
        clip_path = os.path.join(output_dir, f"clip_{i:03d}.mp4")

        print(f"  [Kling] 场景 {i} ({duration}s): {prompt[:50]}...")
        ok, msg = generate_video_clip(
            prompt=prompt,
            output_path=clip_path,
            aspect_ratio=aspect_ratio,
            duration=duration,
            model=model,
        )
        if not ok:
            return False, f"场景 {i} 视频生成失败: {msg}", []
        video_paths.append(clip_path)
        print(f"  [Kling] 场景 {i} 完成: {clip_path}")

    return True, "", video_paths


# =============================================================================
# 4. FFmpeg 合成
# =============================================================================

def concatenate_clips(
    video_paths: list[str],
    output_path: str,
) -> tuple[bool, str]:
    """
    拼接多个视频片段

    Returns:
        (success, message)
    """
    ok, msg = video_compose.concatenate_videos(video_paths, output_path)
    return ok, msg


def mix_audio_video(
    video_path: str,
    audio_path: str,
    output_path: str,
    subtitle_path: Optional[str] = None,
    bgm_path: Optional[str] = None,
    bgm_volume: float = 0.3,
    voice_volume: float = 1.0,
) -> tuple[bool, str]:
    """
    将配音混入视频

    Returns:
        (success, message)
    """
    ok, msg = video_compose.compose_video(
        video_path=video_path,
        audio_path=audio_path,
        subtitle_path=subtitle_path,
        output_path=output_path,
        bgm_path=bgm_path,
        bgm_volume=bgm_volume,
        voice_volume=voice_volume,
    )
    return ok, msg


# =============================================================================
# 5. 完整管线
# =============================================================================

def run_pipeline(
    episode_id: int,
    script_json: str,
    output_dir: str,
    voice: str = "longxiao",
    aspect_ratio: str = "16:9",
    kling_model: str = "c1",
    bgm_path: Optional[str] = None,
    subtitle_path: Optional[str] = None,
    voice_volume: float = 1.0,
    bgm_volume: float = 0.3,
) -> tuple[bool, str, str]:
    """
    运行完整的视频生成管线

    流程:
      1. 解析脚本 → 场景列表
      2. 生成配音 → 多个 .mp3 文件
      3. 生成视频 → 多个 .mp4 文件
      4. 拼接视频 → combined.mp4
      5. 混入音频 → final.mp4

    Args:
        episode_id: 集数 ID（用于日志）
        script_json: 脚本 JSON 字符串
        output_dir: 输出目录
        voice: TTS 语音
        aspect_ratio: Kling 画面比例
        kling_model: Kling 模型
        bgm_path: 背景音乐路径（可选）
        subtitle_path: 字幕文件路径（可选）
        voice_volume: 配音音量
        bgm_volume: BGM 音量

    Returns:
        (success, message, output_path)
        output_path: 最终视频文件路径（失败时为空）
    """
    run_id = uuid.uuid4().hex[:8]
    work_dir = os.path.join(output_dir, f"run_{run_id}")
    os.makedirs(work_dir, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"Video Pipeline [{episode_id}] run={run_id}")
    print(f"{'='*60}")

    try:
        # Step 1: 解析脚本
        print(f"\n[1/5] 解析脚本...")
        scenes = parse_script(script_json)
        print(f"  → {len(scenes)} 个场景")

        # Step 2: 生成配音
        print(f"\n[2/5] 生成配音 (MiniMax TTS)...")
        voice_dir = os.path.join(work_dir, "voices")
        ok, msg, audio_paths = generate_all_voices(scenes, voice_dir, voice=voice)
        if not ok:
            return False, f"TTS 失败: {msg}", ""
        print(f"  → {len(audio_paths)} 个配音文件")

        # Step 3: 生成视频
        print(f"\n[3/5] 生成视频 (Kling API)...")
        clip_dir = os.path.join(work_dir, "clips")
        ok, msg, video_paths = generate_all_video_clips(
            scenes, clip_dir, aspect_ratio=aspect_ratio, model=kling_model
        )
        if not ok:
            return False, f"Kling 失败: {msg}", ""
        print(f"  → {len(video_paths)} 个视频片段")

        # Step 4: 拼接视频
        print(f"\n[4/5] 拼接视频片段...")
        combined_path = os.path.join(work_dir, "combined.mp4")
        ok, msg = concatenate_clips(video_paths, combined_path)
        if not ok:
            return False, f"视频拼接失败: {msg}", ""
        print(f"  → {combined_path}")

        # Step 5: 混入音频 → 最终成片
        print(f"\n[5/5] 混音合成最终成片...")
        final_path = os.path.join(work_dir, "final.mp4")

        # 合并所有配音为一个文件（简单 concat，用列表顺序）
        if len(audio_paths) > 1:
            # 先把所有 mp3 合并
            concat_audio_list = os.path.join(work_dir, "audio_concat.txt")
            with open(concat_audio_list, "w") as f:
                for ap in audio_paths:
                    escaped = ap.replace("'", "'\\''")
                    f.write(f"file '{escaped}'\n")

            full_audio_path = os.path.join(work_dir, "full_audio.mp3")
            ffmpeg = video_compose.get_ffmpeg_binary()
            cmd = [ffmpeg, "-y", "-f", "concat", "-safe", "0",
                   "-i", concat_audio_list, "-acodec", "copy", full_audio_path]
            ok2, err = video_compose.run_ffmpeg(cmd)
            if not ok2:
                # fallback: 用第一个音频
                full_audio_path = audio_paths[0]
        else:
            full_audio_path = audio_paths[0]

        ok, msg = mix_audio_video(
            video_path=combined_path,
            audio_path=full_audio_path,
            output_path=final_path,
            subtitle_path=subtitle_path,
            bgm_path=bgm_path,
            bgm_volume=bgm_volume,
            voice_volume=voice_volume,
        )
        if not ok:
            return False, f"混音失败: {msg}", ""

        # 复制到输出目录
        final_copy = os.path.join(output_dir, f"episode_{episode_id}_final.mp4")
        import shutil
        shutil.copy(final_path, final_copy)

        print(f"\n{'='*60}")
        print(f"✅ 管线完成: {final_copy}")
        print(f"{'='*60}")
        return True, final_copy, final_copy

    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, f"管线异常: {str(e)}", ""


# =============================================================================
# 6. 快速测试（单场景）
# =============================================================================

def test_single_scene(
    prompt: str,
    dialogue: str,
    output_path: str,
    duration: int = 5,
) -> tuple[bool, str]:
    """
    单场景快速测试（配音 + 视频生成，不做合成）

    Returns:
        (success, message)
    """
    print(f"\n[单场景测试] prompt={prompt[:50]}, dialogue={dialogue[:30]}")

    # 配音
    audio_path = output_path + ".voice.mp3"
    ok, msg = generate_voice_for_scene(dialogue, audio_path)
    if not ok:
        return False, f"TTS 失败: {msg}"
    print(f"  ✓ TTS: {audio_path}")

    # 视频
    video_path = output_path + ".clip.mp4"
    ok, msg = generate_video_clip(prompt, video_path, duration=duration)
    if not ok:
        return False, f"Kling 失败: {msg}"
    print(f"  ✓ Kling: {video_path}")

    return True, f"TTS={audio_path}, Kling={video_path}"


if __name__ == "__main__":
    import sys

    print("视频生成管线自检...")
    print()

    # 检查 FFmpeg
    ok, msg = video_compose.check_ffmpeg()
    print(f"FFmpeg: {'✓' if ok else '✗'} {msg}")

    # 检查 Kling API Key
    kling_key = os.environ.get("KLING_API_KEY", "")
    print(f"Kling API Key: {'✓' if kling_key else '✗ (未设置 KLING_API_KEY)'}")

    # 检查 MiniMax API Key
    minimax_key = os.environ.get("MINIMAX_API_KEY", "") or \
                  os.environ.get("MINIMAX_TTS_KEY", "")
    print(f"MiniMax API Key: {'✓' if minimax_key else '✗ (未设置 MINIMAX_API_KEY)'}")

    if not all([ok, kling_key, minimax_key]):
        print("\n⚠️ 缺少依赖，请先配置环境变量")
        sys.exit(1)

    print("\n环境检查通过")
