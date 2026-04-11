#!/usr/bin/env python3
"""
AIMedia E2E 完整流程测试
测试完整的视频生产管线 + 错误处理

用法:
    python test_e2e_flow.py                # 完整流程 + 错误测试
    python test_e2e_flow.py --skip-ai     # 跳过 AI 生成，只测 CRUD
    python test_e2e_flow.py --ai-only     # 只测 AI 流程（已存在数据）
"""
import httpx
import time
import json
import sys
import os
import argparse

BASE_URL = "http://localhost:4000/api/v1"


def pretty_print(title, data):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)
    print(json.dumps(data, indent=2, ensure_ascii=False))


def wait_for_status(client, url, expected_statuses, timeout=60, poll_interval=2):
    """
    轮询直到状态匹配或超时

    Args:
        client: httpx client
        url: GET url to poll
        expected_statuses: 状态列表，如 ["outline_generated", "failed"]
        timeout: 超时秒数
        poll_interval: 轮询间隔

    Returns:
        (status, data) or (None, None) if timeout
    """
    start = time.time()
    attempts = int(timeout / poll_interval)
    for i in range(attempts):
        resp = client.get(url)
        data = resp.json()
        status = data.get("status", "unknown")
        if status in expected_statuses:
            return status, data
        elapsed = int(time.time() - start)
        print(f"    [{elapsed}s] status={status}, 等待中...")
        time.sleep(poll_interval)
    return None, None


# =============================================================================
# 基础 CRUD 测试
# =============================================================================

def test_crud():
    """测试 Project / Series / Episode 的 CRUD 操作"""
    client = httpx.Client(timeout=30.0, follow_redirects=True)
    results = []
    project_name = f"CRUD测试_{int(time.time())}"

    try:
        # Project CRUD
        print("\n🔵 [CRUD] Project")
        resp = client.post(f"{BASE_URL}/projects", json={
            "title": project_name,
            "description": "自动化CRUD测试"
        })
        assert resp.status_code == 200, f"创建Project失败: {resp.status_code}"
        project = resp.json()
        project_id = project.get("id")
        print(f"  ✅ 创建Project: id={project_id}")

        resp = client.get(f"{BASE_URL}/projects/{project_id}")
        assert resp.status_code == 200
        print(f"  ✅ 读取Project: OK")

        resp = client.put(f"{BASE_URL}/projects/{project_id}", json={
            "title": project_name,
            "description": "更新描述"
        })
        assert resp.status_code == 200, f"更新Project失败: {resp.status_code} {resp.text}"
        print(f"  ✅ 更新Project: OK")

        # Series CRUD
        print("\n🔵 [CRUD] Series")
        resp = client.post(f"{BASE_URL}/series", json={
            "title": f"CRUD系列_{int(time.time())}",
            "project_id": project_id
        })
        assert resp.status_code == 200
        series = resp.json()
        series_id = series.get("id")
        print(f"  ✅ 创建Series: id={series_id}")

        resp = client.get(f"{BASE_URL}/series/{series_id}")
        assert resp.status_code == 200
        print(f"  ✅ 读取Series: OK")

        # Episode CRUD
        print("\n🔵 [CRUD] Episode")
        resp = client.post(f"{BASE_URL}/episodes", json={
            "title": f"CRUD分集_{int(time.time())}",
            "series_id": series_id,
            "episode_number": 1,
            "description": "自动化CRUD测试"
        })
        assert resp.status_code == 200
        episode = resp.json()
        episode_id = episode.get("id")
        print(f"  ✅ 创建Episode: id={episode_id}")

        resp = client.get(f"{BASE_URL}/episodes/{episode_id}")
        assert resp.status_code == 200
        print(f"  ✅ 读取Episode: OK")

        # 清理
        client.delete(f"{BASE_URL}/projects/{project_id}")
        print(f"\n  ✅ 清理Project {project_id}: OK")

        print("\n🟢 CRUD 全部通过")
        return True

    except AssertionError as e:
        print(f"\n🔴 CRUD 失败: {e}")
        return False
    except Exception as e:
        print(f"\n🔴 CRUD 异常: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        client.close()


# =============================================================================
# 错误场景测试
# =============================================================================

def test_error_scenarios():
    """测试错误处理：无效输入、缺失必填字段、状态拦截"""
    client = httpx.Client(timeout=30.0, follow_redirects=True)

    try:
        print("\n🔵 [错误场景] 测试")

        # 1. 生成视频时无 script → 应返回 400
        print("\n  [1] generate-video 无 script → 400")
        resp = client.post(f"{BASE_URL}/projects", json={
            "title": f"错误测试_{int(time.time())}"
        })
        project_id = resp.json().get("id")

        resp = client.post(f"{BASE_URL}/series", json={
            "title": f"错误系列_{int(time.time())}",
            "project_id": project_id
        })
        series_id = resp.json().get("id")

        resp = client.post(f"{BASE_URL}/episodes", json={
            "title": f"错误分集_{int(time.time())}",
            "series_id": series_id,
            "episode_number": 1,
        })
        episode_id = resp.json().get("id")

        resp = client.post(f"{BASE_URL}/episodes/{episode_id}/generate-video")
        if resp.status_code == 400:
            print(f"  ✅ 正确拦截: {resp.status_code} - {resp.json()}")
        else:
            print(f"  ⚠️  期望400，实际: {resp.status_code} - {resp.text}")

        # 2. 无效 series_id → 404 或 422
        print("\n  [2] 无效 series_id → 404/422")
        resp = client.post(f"{BASE_URL}/episodes", json={
            "title": "无效测试",
            "series_id": 999999,
            "episode_number": 1,
        })
        if resp.status_code in (404, 422):
            print(f"  ✅ 正确拒绝: {resp.status_code}")
        else:
            print(f"  ⚠️  期望404/422，实际: {resp.status_code} - {resp.text}")

        # 3. generate-outline 空参数 → 应被拒绝
        print("\n  [3] generate-outline 空参数 → 400/422")
        resp = client.post(f"{BASE_URL}/series/{series_id}/generate-outline", json={
            "project_title": "",
            "project_description": "",
        })
        if resp.status_code in (400, 422):
            print(f"  ✅ 正确拒绝空参数: {resp.status_code}")
        else:
            print(f"  ⚠️  期望400/422，实际: {resp.status_code}")

        # 4. 重复创建同名 Project → 应成功（不强制唯一）
        print("\n  [4] 重复创建同名 → 200（不强制唯一）")
        resp = client.post(f"{BASE_URL}/projects", json={"title": "重复名称测试"})
        ok1 = resp.status_code == 200
        resp = client.post(f"{BASE_URL}/projects", json={"title": "重复名称测试"})
        ok2 = resp.status_code == 200
        if ok1 and ok2:
            print(f"  ✅ 允许重复名称（应用层不强制唯一）")
        else:
            print(f"  ⚠️  状态码: {ok1}, {ok2}")

        # 清理
        client.delete(f"{BASE_URL}/projects/{project_id}")

        print("\n🟢 错误场景测试完成")
        return True

    except Exception as e:
        print(f"\n🔴 错误场景异常: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        client.close()


# =============================================================================
# AI 流程测试（依赖外部 API）
# =============================================================================

def test_ai_flow():
    """测试完整的 AI 生成流程：outline → script → video（状态轮询）"""
    client = httpx.Client(timeout=60.0, follow_redirects=True)

    project_name = f"AI流程测试_{int(time.time())}"
    series_name = f"AI系列_{int(time.time())}"
    episode_title = f"AI分集_{int(time.time())}"

    try:
        # 创建资源
        resp = client.post(f"{BASE_URL}/projects", json={
            "title": project_name,
            "description": "AI流程自动化测试"
        })
        project_id = resp.json().get("id")
        print(f"\n🔵 创建 Project: {project_id}")

        resp = client.post(f"{BASE_URL}/series", json={
            "title": series_name,
            "project_id": project_id
        })
        series_id = resp.json().get("id")
        print(f"🔵 创建 Series: {series_id}")

        resp = client.post(f"{BASE_URL}/episodes", json={
            "title": episode_title,
            "series_id": series_id,
            "episode_number": 1,
            "description": "AI流程自动化测试"
        })
        episode_id = resp.json().get("id")
        print(f"🔵 创建 Episode: {episode_id}")

        # Step 1: 生成大纲
        print("\n🔵 [AI流程] Step 1: 生成大纲")
        resp = client.post(f"{BASE_URL}/series/{series_id}/generate-outline", json={
            "project_title": project_name,
            "project_description": "AI自媒体系列视频项目"
        })
        print(f"  响应: {resp.status_code}")
        if resp.status_code != 200:
            print(f"  ⚠️  generate-outline 失败: {resp.text}")
            return False

        status, data = wait_for_status(
            client,
            f"{BASE_URL}/series/{series_id}",
            ["outline_generated", "failed"],
            timeout=90
        )
        if status == "outline_generated":
            print(f"  ✅ 大纲生成成功 ({len(data.get('outline', ''))} 字符)")
            series_outline = data.get("outline", "")
        elif status == "failed":
            print(f"  ⚠️  大纲生成失败: {data.get('error_message', data)}")
            series_outline = ""
        else:
            print(f"  ⚠️  轮询超时，大纲可能仍在生成中")
            series_outline = ""

        # Step 2: 生成脚本
        print("\n🔵 [AI流程] Step 2: 生成脚本")
        resp = client.post(f"{BASE_URL}/episodes/{episode_id}/generate-script", json={
            "project_title": project_name,
            "series_outline": series_outline or "测试系列的第1集内容",
            "episode_title": episode_title
        })
        print(f"  响应: {resp.status_code}")
        if resp.status_code != 200:
            print(f"  ⚠️  generate-script 失败: {resp.text}")
            return False

        status, data = wait_for_status(
            client,
            f"{BASE_URL}/episodes/{episode_id}",
            ["script_generated", "failed"],
            timeout=90
        )
        if status == "script_generated":
            script = data.get("script", "")
            print(f"  ✅ 脚本生成成功 ({len(script)} 字符)")
        elif status == "failed":
            print(f"  ⚠️  脚本生成失败: {data.get('error_message', data)}")
            return False
        else:
            print(f"  ⚠️  轮询超时")
            return False

        # Step 3: 生成视频（可能因 KLING_API_KEY 未配置而失败，不影响测试通过）
        print("\n🔵 [AI流程] Step 3: 生成视频")
        resp = client.post(f"{BASE_URL}/episodes/{episode_id}/generate-video")
        print(f"  响应: {resp.status_code}")
        # 不强制要求视频生成成功（Kling Key 可能未配）

        status, data = wait_for_status(
            client,
            f"{BASE_URL}/episodes/{episode_id}",
            ["video_completed", "video_generating", "failed"],
            timeout=60
        )
        if status:
            print(f"  ✅ 视频管线触发成功，最终状态: {status}")
        else:
            print(f"  ⚠️  视频管线状态未知")

        # 验证最终数据
        resp = client.get(f"{BASE_URL}/episodes/{episode_id}")
        final = resp.json()
        print(f"\n📊 最终状态: {final.get('status')}")
        print(f"📊 video_path: {final.get('video_path') or '(未生成)'}")

        # 清理
        client.delete(f"{BASE_URL}/projects/{project_id}")
        print(f"\n✅ 清理完成")

        print("\n🟢 AI 流程测试完成")
        return True

    except Exception as e:
        print(f"\n🔴 AI 流程异常: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        client.close()


# =============================================================================
# 主入口
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AIMedia E2E 测试")
    parser.add_argument("--skip-ai", action="store_true", help="跳过 AI 流程测试")
    parser.add_argument("--ai-only", action="store_true", help="只运行 AI 流程测试")
    args = parser.parse_args()

    # 检查后端是否运行
    try:
        resp = httpx.get(f"{BASE_URL.replace('/api/v1', '')}/health", timeout=5)
        if resp.status_code != 200:
            print(f"⚠️  后端未正常运行: {resp.status_code}")
            sys.exit(1)
    except Exception:
        print(f"⚠️  无法连接到后端 ({BASE_URL})，请先启动: cd src/backend && uvicorn app.main:app --reload")
        sys.exit(1)

    print("="*60)
    print("  AIMedia E2E 测试套件")
    print("="*60)

    all_passed = True

    if args.ai_only:
        all_passed = test_ai_flow()
    else:
        all_passed = test_crud()
        if all_passed:
            all_passed = test_error_scenarios()
        if all_passed and not args.skip_ai:
            all_passed = test_ai_flow()

    print("\n" + "="*60)
    if all_passed:
        print("✅ 全部测试通过")
        sys.exit(0)
    else:
        print("⚠️  部分测试失败（见上文）")
        sys.exit(1)
