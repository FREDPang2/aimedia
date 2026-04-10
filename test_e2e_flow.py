#!/usr/bin/env python3
"""
AIMedia E2E 完整流程测试
测试完整的视频生产管线：Project → Series → Episode → Video Generation
"""
import httpx
import time
import json
import sys

BASE_URL = "http://localhost:4000/api/v1"

def pretty_print(title, data):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)
    print(json.dumps(data, indent=2, ensure_ascii=False))

def test_flow():
    client = httpx.Client(timeout=60.0, follow_redirects=True)
    
    # 测试数据
    project_name = f"E2E测试项目_{int(time.time())}"
    series_name = f"E2E测试系列_{int(time.time())}"
    episode_title = f"E2E测试分集_{int(time.time())}"
    
    try:
        # Step 1: 创建 Project
        print("\n🔵 Step 1: 创建 Project")
        resp = client.post(f"{BASE_URL}/projects", json={
            "title": project_name,
            "description": "E2E自动化测试项目"
        })
        print(f"Status: {resp.status_code}")
        project = resp.json()
        project_id = project.get("id")
        pretty_print("Project 创建成功", project)
        
        # Step 2: 创建 Series (关联 Project)
        print("\n🔵 Step 2: 创建 Series")
        resp = client.post(f"{BASE_URL}/series", json={
            "title": series_name,
            "project_id": project_id
        })
        print(f"Status: {resp.status_code}")
        series = resp.json()
        series_id = series.get("id")
        pretty_print("Series 创建成功", series)
        
        # Step 3: 调用 generate-outline
        print("\n🔵 Step 3: 调用 generate-outline")
        resp = client.post(f"{BASE_URL}/series/{series_id}/generate-outline", json={
            "project_title": project_name,
            "project_description": "AI自媒体系列视频项目"
        })
        print(f"Status: {resp.status_code}")
        result = resp.json()
        pretty_print("Outline 生成请求已提交", result)
        
        # 轮询检查 outline 生成状态
        print("\n🔵 轮询 Series 状态...")
        max_attempts = 30  # Wait up to 60 seconds for outline
        for i in range(max_attempts):
            time.sleep(2)
            resp = client.get(f"{BASE_URL}/series/{series_id}")
            series_status = resp.json()
            status = series_status.get("status", "unknown")
            outline = series_status.get("outline", "") or ""
            print(f"  [{i+1}/{max_attempts}] status={status}, outline长度={len(outline)}")
            # Wait for actual content, not just status
            if outline and len(outline) > 50:
                pretty_print("Outline 生成完成", series_status)
                break
        else:
            print(f"⚠️ 等待 {max_attempts*2} 秒后 outline 仍为空或过短")
        
        # Step 4: 创建 Episode (关联 Series)
        print("\n🔵 Step 4: 创建 Episode")
        resp = client.post(f"{BASE_URL}/episodes", json={
            "title": episode_title,
            "series_id": series_id,
            "episode_number": 1,
            "description": "E2E自动化测试分集"
        })
        print(f"Status: {resp.status_code}")
        episode = resp.json()
        episode_id = episode.get("id")
        pretty_print("Episode 创建成功", episode)
        
        # Step 5: 调用 generate-script
        print("\n🔵 Step 5: 调用 generate-script")
        resp = client.post(f"{BASE_URL}/episodes/{episode_id}/generate-script", json={
            "project_title": project_name,
            "series_outline": series_status.get("outline", ""),
            "episode_title": episode_title
        })
        print(f"Status: {resp.status_code}")
        result = resp.json()
        pretty_print("Script 生成请求已提交", result)
        
        # 轮询检查 script 生成状态
        print("\n🔵 轮询 Episode Script 状态...")
        for i in range(20):
            time.sleep(2)
            resp = client.get(f"{BASE_URL}/episodes/{episode_id}")
            episode_status = resp.json()
            status = episode_status.get("status", "unknown")
            script = episode_status.get("script", "")
            print(f"  [{i+1}] status={status}, script长度={len(script) if script else 0}")
            if "script" in status or status == "script_generated":
                pretty_print("Script 生成完成", episode_status)
                break
        
        # Step 6: 调用 generate-video
        print("\n🔵 Step 6: 调用 generate-video")
        resp = client.post(f"{BASE_URL}/episodes/{episode_id}/generate-video")
        print(f"Status: {resp.status_code}")
        result = resp.json()
        pretty_print("Video 生成请求已提交", result)
        
        # 轮询检查 video 生成状态
        print("\n🔵 轮询 Episode Video 状态...")
        for i in range(30):
            time.sleep(3)
            resp = client.get(f"{BASE_URL}/episodes/{episode_id}")
            episode_status = resp.json()
            status = episode_status.get("status", "unknown")
            video_path = episode_status.get("video_path", "")
            print(f"  [{i+1}] status={status}, video_path={video_path or 'None'}")
            if "video" in status or status == "video_completed":
                pretty_print("Video 生成完成", episode_status)
                break
            if status == "failed":
                print("❌ Video 生成失败")
                break
        
        # Step 7: 验证 episode.video_path
        print("\n🔵 Step 7: 验证 video_path")
        resp = client.get(f"{BASE_URL}/episodes/{episode_id}")
        final_episode = resp.json()
        video_path = final_episode.get("video_path", "")
        print(f"video_path: {video_path}")
        
        if video_path:
            import os
            if os.path.exists(video_path):
                print(f"✅ Video 文件存在: {video_path}")
            else:
                print(f"⚠️ Video 路径已记录但文件不存在: {video_path}")
        else:
            print("⚠️ Video 路径为空（可能 KLING_API_KEY 未配置）")
        
        pretty_print("最终 Episode 状态", final_episode)
        
        # 清理测试数据
        print("\n🔵 清理测试数据...")
        client.delete(f"{BASE_URL}/projects/{project_id}")
        print(f"✅ 已删除 Project {project_id}")
        
        print("\n" + "="*60)
        print("  E2E 流程测试完成")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        client.close()

if __name__ == "__main__":
    test_flow()
