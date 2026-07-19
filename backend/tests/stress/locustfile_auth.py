"""
场景A：认证压测
测试注册、登录、获取个人信息

运行：
    python -m locust -f locustfile_auth.py --host=http://localhost:8000
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from backend.tests.stress.scenarios.auth_scenario import AuthStressUser
