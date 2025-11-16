import requests
import json
from datetime import datetime, timedelta



# 登录获取访问令牌
def get_access_token():
    login_url = 'http://localhost:5000/api/login'
    login_data = {
        'username': 'wyl',
        'password': 'upshalks123'  # 使用符合要求的密码
    }
    response = requests.post(login_url, json=login_data)
    if response.status_code == 200:
        data = response.json()
        print(f"登录成功，用户ID: {data.get('user_id')}")
        return data.get('access_token'), data.get('user_id')
    else:
        print(f"登录失败: {response.status_code} - {response.text}")
        return None, None

# 创建一个立即到期的任务
def create_test_task(token):
    if not token:
        return
    
    todos_url = 'http://localhost:5000/api/todos'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # 创建立即到期的任务（当前时间）
    due_date = datetime.utcnow().isoformat() + 'Z'
    task_data = {
        'title': '立即到期测试任务',
        'description': '这是一个立即到期的测试任务，用于测试提醒功能',
        'due_date': due_date,
        'priority': 1,
        'completed': False,
        'tags':['1']
    }
    
    response = requests.post(todos_url, json=task_data, headers=headers)
    if response.status_code == 201:
        print("任务创建成功!")
        print(f"任务信息: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.json().get('id')
    else:
        print(f"任务创建失败: {response.status_code} - {response.text}")
        return None

# 触发提醒检查
def trigger_reminder_check():
    test_url = 'http://localhost:5000/api/todos/upcoming'
    response = requests.get(test_url)
    print(f"提醒检查触发响应: {response.status_code} - {response.text}")

if __name__ == "__main__":
    # 登录获取令牌和用户ID
    token, user_id = get_access_token()

    if token:
        # 创建立即到期的测试任务
        task_id = create_test_task(token)

        if task_id:
            # 手动触发提醒检查
            trigger_reminder_check()