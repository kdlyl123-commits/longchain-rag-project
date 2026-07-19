"""
场景C：管理员知识库压测
测试文档列表、统计查询、文件上传

运行：
    python -m locust -f locustfile_admin.py --host=http://localhost:8000
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from backend.tests.stress.scenarios.rag_scenario import AdminDocStressUser
