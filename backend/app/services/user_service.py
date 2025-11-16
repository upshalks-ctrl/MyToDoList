from backend.app import bcrypt, db
from backend.app.models.models import User
from backend.app.schems import UserSchema
from backend.app.services.todo_service import delete_old_completed_tasks
from marshmallow import ValidationError

def get_user_by_id(user_id):
    """
    根据用户ID获取用户信息
    """
    return User.query.get(user_id)

def get_user_by_username(username):
    """
    根据用户名获取用户信息
    """
    return User.query.filter_by(username=username).first()

def create_user(username, password):
    """
    创建新用户
    """
    # 使用schema验证输入数据
    user_schema = UserSchema()
    try:
        # 验证数据
        user_data = user_schema.load({'username': username, 'password': password})
    except ValidationError as err:
        raise ValueError(err.messages)
    
    # 检查用户名是否已存在
    existing_user = get_user_by_username(username)
    if existing_user:
        raise ValueError('Username already exists')
    
    # 创建新用户
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(username=username, password=hashed_password)
    
    # 添加到数据库
    db.session.add(new_user)
    db.session.commit()
    
    return new_user

def authenticate_user(username, password):
    """
    验证用户身份
    """
    user = get_user_by_username(username)
    if user and bcrypt.check_password_hash(user.password, password):
        # 在用户登录时删除24小时前已完成的任务
        delete_old_completed_tasks(user.id)
        return user
    return None