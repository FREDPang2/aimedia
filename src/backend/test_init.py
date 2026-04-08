#!/usr/bin/env python3
"""测试 AIMedia 后端"""

import sys
sys.path.insert(0, '.')

# 测试数据库
print("=== 测试数据库初始化 ===")
from database import init_database
init_database()
print("✅ 数据库初始化成功")

# 测试模型导入
print("\n=== 测试模型导入 ===")
from models import Project, Series, Episode, VideoTask
print("✅ 模型导入成功")

# 测试 FastAPI 应用
print("\n=== 测试 FastAPI 应用 ===")
from app.main import app
print(f"✅ FastAPI 应用: {app.title}")
print(f"✅ 版本: {app.version}")
print(f"✅ 路由数量: {len(app.routes)}")

# 列出所有路由
print("\n=== API 路由 ===")
for route in app.routes:
    if hasattr(route, 'path'):
        methods = getattr(route, 'methods', {'GET'})
        print(f"  {list(methods)[0] if methods else 'GET'}: {route.path}")

print("\n✅ 所有测试通过!")
