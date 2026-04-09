"""
AI Workflow Service - 使用 Moonshot (Kimi) API 生成系列大纲、单集提纲、脚本和分镜
"""
import httpx

MOONSHOT_API_KEY = "sk-kimi-o5EGW4ylRMFuVdDYa3r6UxBwBPFoegzWxKv4svrjsV7bolyRADdXrbNqVjsuwYUx"
MOONSHOT_BASE_URL = "https://api.moonshot.cn/v1"


async def call_moonshot(prompt: str, model: str = "moonshot-v1-8k") -> str:
    """调用 Moonshot API 生成内容"""
    async with httpx.AsyncClient(proxy="http://172.29.112.1:7897", timeout=120.0) as client:
        response = await client.post(
            f"{MOONSHOT_BASE_URL}/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {MOONSHOT_API_KEY}"
            },
            json={
                "model": model,
                "max_tokens": 4096,
                "messages": [{"role": "user", "content": prompt}]
            }
        )
        data = response.json()
        return data["choices"][0]["message"]["content"]


async def create_series_outline(
    project_id: int,
    project_title: str = "",
    project_description: str = "",
    episode_count: int = 5
) -> dict:
    """
    使用 Moonshot API 生成系列大纲
    """
    prompt = f"""请为项目「{project_title}」生成系列大纲。

项目描述：{project_description or '暂无描述'}
计划集数：{episode_count} 集

请生成一个包含 {episode_count} 集的系列大纲，每集需要一个简短的主题和核心内容概述。
以 JSON 格式返回，包含 series_outline（总体概述）和 episodes（每集信息数组，每项包含 episode_number、title、brief）。"""
    content = await call_moonshot(prompt, model="moonshot-v1-8k")
    return {"project_id": project_id, "outline": content}


async def create_episode_outline(
    episode_id: int,
    episode_title: str = "",
    episode_number: int = 1,
    series_outline: str = ""
) -> dict:
    """
    使用 Moonshot API 生成单集详细提纲
    """
    prompt = f"""请为系列中的第 {episode_number} 集「{episode_title}」生成详细的单集提纲。

系列大纲：{series_outline or '暂无系列大纲'}

请生成包含以下内容的单集提纲：
1. 集数：第 {episode_number} 集
2. 标题：{episode_title}
3. 核心冲突/亮点
4. 主要情节点（分 3-5 个场景）
5. 结尾悬念/总结

以 JSON 格式返回，包含 episode_number、title、core_conflict、scenes（场景数组）、ending_note。"""
    content = await call_moonshot(prompt, model="moonshot-v1-8k")
    return {"episode_id": episode_id, "outline": content}


async def create_script_storyboard(
    episode_id: int,
    episode_title: str = "",
    episode_number: int = 1,
    episode_outline: str = ""
) -> dict:
    """
    使用 Moonshot API 生成完整脚本和分镜
    """
    prompt = f"""请为第 {episode_number} 集「{episode_title}」生成完整的视频脚本和分镜描述。

单集提纲：{episode_outline or '暂无提纲'}

请生成包含以下内容的完整脚本：
1. 分镜描述（每场场景的时间、人物、动作、画面描述）
2. 完整对白/配音稿
3. 背景音乐/音效提示
4. 镜头运动说明

以 JSON 格式返回，包含 scenes（分镜数组，每项含 timecode、character、action、dialogue、music_effects、camera_movement）和 full_script（完整文案）。"""
    content = await call_moonshot(prompt, model="moonshot-v1-32k")
    return {"episode_id": episode_id, "script": content}
