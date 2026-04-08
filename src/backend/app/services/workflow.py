"""
AI Workflow Service - 使用 Kimi 生成系列大纲、单集提纲、脚本和分镜
"""
import httpx

KIMI_API_KEY = "sk-kimi-o5EGW4ylRMFuVdDYa3r6UxBwBPFoegzWxKv4svrjsV7bolyRADdXrbNqVjsuwYUx"
KIMI_BASE_URL = "https://api.kimi.com/coding"


async def call_kimi(prompt: str) -> str:
    """调用 Kimi API 生成内容"""
    async with httpx.AsyncClient(proxy="http://172.29.112.1:7897") as client:
        response = await client.post(
            f"{KIMI_BASE_URL}/v1/messages",
            headers={
                "Content-Type": "application/json",
                "x-api-key": KIMI_API_KEY,
                "anthropic-version": "2023-06-01"
            },
            json={
                "model": "kimi-code",
                "max_tokens": 4096,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=60.0
        )
        return response.json()["content"][0]["text"]


async def create_series_outline(project_id: int) -> dict:
    """
    使用 Kimi 生成系列大纲
    """
    prompt = f"请为项目 {project_id} 生成系列大纲"
    content = await call_kimi(prompt)
    return {"project_id": project_id, "outline": content}


async def create_episode_outline(episode_id: int) -> dict:
    """
    使用 Kimi 生成单集详细提纲
    """
    prompt = f"请为剧集 {episode_id} 生成单集详细提纲"
    content = await call_kimi(prompt)
    return {"episode_id": episode_id, "outline": content}


async def create_script_storyboard(episode_id: int) -> dict:
    """
    使用 Kimi 生成完整脚本和分镜
    """
    prompt = f"请为剧集 {episode_id} 生成完整脚本和分镜"
    content = await call_kimi(prompt)
    return {"episode_id": episode_id, "script": content}
