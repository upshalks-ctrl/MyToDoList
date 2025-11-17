import requests
import json
import time

# 测试用户信息
TEST_USERNAME = "testuser"
TEST_PASSWORD = "Password123"
API_BASE_URL = "http://localhost:5000/api"

# 注册用户
def register_user():
    register_url = f"{API_BASE_URL}/register"
    response = requests.post(register_url, json={
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD
    })
    if response.status_code == 201:
        print(f"用户注册成功: {TEST_USERNAME}")
        return True
    elif response.status_code == 400:
        print(f"用户已存在: {TEST_USERNAME}")
        return True
    else:
        print(f"用户注册失败: {response.status_code} {response.text}")
        return False

# 获取访问令牌
def get_access_token():
    login_url = f"{API_BASE_URL}/login"
    response = requests.post(login_url, json={
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"登录失败: {response.status_code} {response.text}")
        return None

# 创建测试任务
def create_test_task(token):
    create_url = f"{API_BASE_URL}/todos"
    headers = {"Authorization": f"Bearer {token}"}
    
    # 创建一个立即到期的任务
    task_data = {
        "title": "测试通知点击功能",
        "description": "这是一个用于测试点击通知显示任务详情功能的测试任务",
        "due_date": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
        "priority": "high",
        "tags": []
    }
    
    response = requests.post(create_url, headers=headers, json=task_data)
    if response.status_code == 201:
        task = response.json()
        print(f"创建任务成功: {task['title']} (ID: {task['id']})")
        return task
    else:
        print(f"创建任务失败: {response.status_code} {response.text}")
        return None

# 触发提醒检查
def trigger_reminder_check(token):
    reminder_url = f"{API_BASE_URL}/test/reminder"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(reminder_url, headers=headers)
    if response.status_code == 200:
        print("触发提醒检查成功")
        return response.json()
    else:
        print(f"触发提醒检查失败: {response.status_code} {response.text}")
        return None

# 主函数
def main():
    print("测试通知点击功能...")
    
    # 1. 注册用户（如果不存在）
    if not register_user():
        return
    
    # 2. 获取访问令牌
    token = get_access_token()
    if not token:
        return
    
    # 2. 创建测试任务
    task = create_test_task(token)
    if not task:
        return
    
    # 3. 触发提醒检查
    time.sleep(1)  # 等待任务创建完成
    result = trigger_reminder_check(token)
    
    if result and result["status"] == "success":
        print(f"\n测试任务信息:")
        print(f"  任务ID: {task['id']}")
        print(f"  任务标题: {task['title']}")
        print(f"  任务描述: {task['description']}")
        print(f"  截止时间: {task['due_date']}")
        print(f"  优先级: {task['priority']}")
        print(f"\n✓ 测试成功！请在前端页面点击消息通知查看任务详情。")
    else:
        print("✗ 测试失败")

if __name__ == "__main__":
    main()