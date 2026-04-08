"""
可灵 (Kling) 视频生成 API 服务
"""

import httpx
import os
import time
from typing import Optional

# API 配置
KLING_API_KEY = os.environ.get("KLING_API_KEY", "")
KLING_BASE_URL = "https://api.klingai.com/v1"

# 错误类
class KlingError(Exception):
    def __init__(self, message: str, code: Optional[str] = None):
        self.message = message
        self.code = code
        super().__init__(self.message)


def generate_video(
    prompt: str,
    aspect_ratio: str = "16:9",
    duration: int = 5,
    **kwargs
) -> str:
    """
    提交视频生成任务
    
    Args:
        prompt: 视频描述prompt
        aspect_ratio: 画面比例 (16:9, 9:16)
        duration: 时长(秒)
        
    Returns:
        task_id: 任务ID
    """
    if not KLING_API_KEY:
        raise KlingError("KLING_API_KEY not set")
    
    url = f"{KLING_BASE_URL}/videos/generate"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {KLING_API_KEY}"
    }
    payload = {
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "duration": duration,
        **kwargs
    }
    
    # 清理空值
    payload = {k: v for k, v in payload.items() if v is not None}
    
    with httpx.Client(timeout=30.0) as client:
        response = client.post(url, json=payload, headers=headers)
        
    if response.status_code != 200:
        raise KlingError(f"API error: {response.status_code}", code=str(response.status_code))
    
    result = response.json()
    
    if "data" not in result or "task_id" not in result.get("data", {}):
        raise KlingError(f"Invalid response: {result}")
    
    return result["data"]["task_id"]


def check_status(task_id: str) -> dict:
    """
    查询任务状态
    
    Args:
        task_id: 任务ID
        
    Returns:
        status: pending/processing/completed/failed
        video_url: 完成时的视频URL
    """
    if not KLING_API_KEY:
        raise KlingError("KLING_API_KEY not set")
    
    url = f"{KLING_BASE_URL}/videos/status/{task_id}"
    headers = {
        "Authorization": f"Bearer {KLING_API_KEY}"
    }
    
    with httpx.Client(timeout=30.0) as client:
        response = client.get(url, headers=headers)
    
    if response.status_code != 200:
        raise KlingError(f"API error: {response.status_code}", code=str(response.status_code))
    
    result = response.json()
    data = result.get("data", {})
    
    return {
        "status": data.get("status", "unknown"),
        "video_url": data.get("video_url"),
        "cover_url": data.get("cover_url"),
        "error": data.get("error")
    }


def wait_for_completion(
    task_id: str,
    max_wait: int = 600,
    poll_interval: int = 5
) -> dict:
    """
    轮询等待视频生成完成
    
    Args:
        task_id: 任务ID
        max_wait: 最大等待时间(秒)
        poll_interval: 轮询间隔(秒)
        
    Returns:
        最终状态dict
    """
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        status = check_status(task_id)
        
        if status["status"] in ("completed", "failed"):
            return status
        
        time.sleep(poll_interval)
    
    return {"status": "timeout", "task_id": task_id}
