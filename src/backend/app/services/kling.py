"""
Kling AI (可灵) 视频生成服务
支持文生视频 (Text-to-Video) API

API 文档: https://www.klingai.com
"""
import os
import time
import requests
from typing import Optional

# Kling API 配置
KLING_API_KEY = os.environ.get("KLING_API_KEY", "")
KLING_BASE_URL = "https://api.klingai.com"

# WSL2 代理（访问国内 API）
PROXY = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or \
        os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy", "")

# 默认参数
DEFAULT_ASPECT = "16:9"  # 横屏，可选 "9:16" 竖屏
DEFAULT_DURATION = 5     # 5秒，可选 10
DEFAULT_MODEL = "c1"      # 标准画质，可选 "c1" 标准 / "h2" 高清


def _get_session() -> requests.Session:
    """创建带代理的请求 session"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {KLING_API_KEY}",
    })
    if PROXY:
        session.proxies = {
            "http": PROXY,
            "https": PROXY,
        }
    return session


def create_text2video_task(
    prompt: str,
    aspect_ratio: str = DEFAULT_ASPECT,
    duration: int = DEFAULT_DURATION,
    model: str = DEFAULT_MODEL,
    negative_prompt: str = "",
    cfg_scale: float = 1.0,
) -> dict:
    """
    创建文生视频任务

    Args:
        prompt: 视频描述文本（中文效果最佳）
        aspect_ratio: 画面比例，"16:9" 横屏 或 "9:16" 竖屏
        duration: 视频时长（秒），默认 5 秒
        model: 模型版本，"c1" 标准 / "h2" 高清
        negative_prompt: 负面提示词（不希望出现的元素）
        cfg_scale: 提示词相关性强度（1.0-2.0）

    Returns:
        dict: 包含 task_id 的响应，格式 {"task_id": "xxx", ...}

    Raises:
        ValueError: API Key 未设置或请求失败
    """
    if not KLING_API_KEY:
        raise ValueError("KLING_API_KEY 环境变量未设置")

    url = f"{KLING_BASE_URL}/v1/videos/text2video"
    payload = {
        "model": model,
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "duration": duration,
        "negative_prompt": negative_prompt,
        "cfg_scale": cfg_scale,
        "source_version": "v2",
        "ai_dynamic_level": "v1",
    }

    # 清理空字段
    payload = {k: v for k, v in payload.items() if v}

    session = _get_session()
    for attempt in range(3):
        try:
            resp = session.post(url, json=payload, timeout=30)
            data = resp.json()
            if resp.status_code == 200:
                if "data" in data and "task_id" in data["data"]:
                    return data["data"]
                elif "task_id" in data:
                    return data
                raise ValueError(f"Kling API 响应格式异常: {data}")
            else:
                err_msg = data.get("message", data.get("error", str(data)))
                print(f"[kling] attempt {attempt + 1} failed: {resp.status_code} {err_msg}")
                if resp.status_code in (400, 401, 403):
                    raise ValueError(f"Kling API 认证失败: {err_msg}")
        except requests.exceptions.RequestException as e:
            print(f"[kling] attempt {attempt + 1} network error: {e}")

    raise ValueError("Kling API 文生视频任务创建失败")


def query_task_status(task_id: str) -> dict:
    """
    查询视频生成任务状态

    Returns:
        dict: 状态信息，包含:
            - task_id: 任务ID
            - status: "pending" | "processing" | "completed" | "failed"
            - video_url: 完成时的视频URL（仅 completed 时有）
            - cover_url: 封面URL
            - error: 错误信息（仅 failed 时有）
    """
    if not KLING_API_KEY:
        raise ValueError("KLING_API_KEY 环境变量未设置")

    url = f"{KLING_BASE_URL}/v1/videos/{task_id}"
    session = _get_session()

    for attempt in range(3):
        try:
            resp = session.get(url, timeout=30)
            data = resp.json()
            if resp.status_code == 200:
                return data.get("data", data)
            else:
                print(f"[kling] query attempt {attempt + 1} failed: {resp.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"[kling] query attempt {attempt + 1} network error: {e}")

    raise ValueError(f"查询 Kling 任务状态失败: {task_id}")


def wait_for_completion(
    task_id: str,
    poll_interval: float = 5.0,
    max_wait: float = 300.0,
) -> dict:
    """
    轮询等待视频生成完成

    Args:
        task_id: 任务ID
        poll_interval: 轮询间隔（秒）
        max_wait: 最大等待时间（秒）

    Returns:
        dict: 完成状态信息（含 video_url）

    Raises:
        TimeoutError: 等待超时
        ValueError: 任务失败
    """
    start = time.time()
    while time.time() - start < max_wait:
        result = query_task_status(task_id)
        status = result.get("status", "")
        print(f"[kling] task {task_id} status: {status}")

        if status == "completed":
            return result
        elif status == "failed":
            raise ValueError(f"Kling 视频生成失败: {result.get('error', 'unknown')}")

        time.sleep(poll_interval)

    raise TimeoutError(f"Kling 任务等待超时 ({max_wait}s): {task_id}")


def download_video(url: str, output_path: str) -> bool:
    """
    下载视频文件

    Args:
        url: 视频直链
        output_path: 保存路径

    Returns:
        bool: 下载是否成功
    """
    session = _get_session()
    for attempt in range(3):
        try:
            resp = session.get(url, timeout=120, stream=True)
            if resp.status_code == 200:
                os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
                with open(output_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=65536):
                        f.write(chunk)
                return True
            else:
                print(f"[kling] download attempt {attempt + 1} failed: {resp.status_code}")
        except Exception as e:
            print(f"[kling] download attempt {attempt + 1} error: {e}")

    return False


def generate_video(
    prompt: str,
    output_path: str,
    aspect_ratio: str = DEFAULT_ASPECT,
    duration: int = DEFAULT_DURATION,
    model: str = DEFAULT_MODEL,
    poll_interval: float = 5.0,
    max_wait: float = 300.0,
) -> tuple[bool, str]:
    """
    完整的文生视频流程：创建任务 → 轮询 → 下载

    Args:
        prompt: 视频描述文本
        output_path: 输出视频文件路径
        aspect_ratio: 画面比例
        duration: 视频时长（秒）
        model: 模型版本
        poll_interval: 轮询间隔
        max_wait: 最大等待时间

    Returns:
        (success, message)
    """
    try:
        # 1. 创建任务
        print(f"[kling] Creating text2video task: {prompt[:50]}...")
        task = create_text2video_task(prompt, aspect_ratio, duration, model)
        task_id = task.get("task_id")
        print(f"[kling] Task created: {task_id}")

        # 2. 轮询等待完成
        result = wait_for_completion(task_id, poll_interval, max_wait)

        # 3. 下载视频
        video_url = result.get("video_url") or result.get("url")
        if not video_url:
            return False, f"任务完成但无视频URL: {result}"

        print(f"[kling] Downloading video from: {video_url}")
        ok = download_video(video_url, output_path)
        if ok:
            return True, output_path
        else:
            return False, "视频下载失败"

    except Exception as e:
        return False, f"[kling] {str(e)}"


if __name__ == "__main__":
    import sys

    if not KLING_API_KEY:
        print("⚠️ KLING_API_KEY 未设置，跳过真实API测试")
        print("   请设置: export KLING_API_KEY=your_key")
        sys.exit(0)

    # 测试：生成一个简单视频片段
    test_prompt = "一只可爱的橘猫在阳光下伸懒腰，背景是花园，温暖柔和的光线"
    output = "/tmp/test_kling_video.mp4"

    print(f"测试 Kling 文生视频 API...")
    success, msg = generate_video(
        prompt=test_prompt,
        output_path=output,
        aspect_ratio="16:9",
        duration=5,
    )
    print(f"结果: success={success}, msg={msg}")
