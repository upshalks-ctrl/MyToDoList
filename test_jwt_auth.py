import requests
import json

# 测试注册新用户
def test_register():
    print("=== 测试注册功能 ===")
    url = "http://localhost:5000/api/register"
    data = {
        "username": "testuser",
        "password": "testpassword"
    }
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, data=json.dumps(data), headers=headers)
    print(f"注册响应状态码: {response.status_code}")
    print(f"注册响应内容: {response.text}")
    print()

# 测试登录功能
def test_login():
    print("=== 测试登录功能 ===")
    url = "http://localhost:5000/api/login"
    data = {
        "username": "testuser",
        "password": "testpassword"
    }
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, data=json.dumps(data), headers=headers)
    print(f"登录响应状态码: {response.status_code}")
    print(f"登录响应内容: {response.text}")
    
    if response.status_code == 200:
        return response.json().get("access_token")
    return None

# 测试使用JWT访问受保护资源
def test_protected_resource(token):
    if not token:
        print("没有获取到token，无法测试受保护资源")
        return
    
    print("=== 测试访问受保护资源 ===")
    url = "http://localhost:5000/api/user"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(url, headers=headers)
    print(f"访问受保护资源响应状态码: {response.status_code}")
    print(f"访问受保护资源响应内容: {response.text}")
    print()

if __name__ == "__main__":
    # 先测试注册
    test_register()
    
    # 然后测试登录
    token = test_login()
    
    # 最后测试访问受保护资源
    test_protected_resource(token)