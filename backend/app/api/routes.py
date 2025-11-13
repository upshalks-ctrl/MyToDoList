from flask import Blueprint, request, jsonify

from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import datetime

from backend.app import bcrypt, db
from backend.app.models.models import User, Todo, Tag, todo_tags

# 创建蓝图
api_bp = Blueprint('api', __name__)

# 注册路由
@api_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # 检查用户名是否已存在
    existing_user = User.query.filter_by(username=data['username']).first()
    if existing_user:
        return jsonify({'message': 'Username already exists'}), 400
    
    # 创建新用户
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(username=data['username'], password=hashed_password)
    
    # 添加到数据库
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'User created successfully'}), 201

# 登录路由
@api_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # 查找用户
    user = User.query.filter_by(username=data['username']).first()
    
    # 检查用户是否存在且密码正确
    if not user or not bcrypt.check_password_hash(user.password, data['password']):
        return jsonify({'message': 'Invalid username or password'}), 401
    
    # 创建访问令牌
    access_token = create_access_token(identity=str(user.id), expires_delta=datetime.timedelta(hours=1))
    
    return jsonify({'access_token': access_token, 'user_id': user.id}), 200

# 获取当前用户信息
@api_bp.route('/user', methods=['GET'])
@jwt_required()
def get_current_user():
    try:
        user_id = get_jwt_identity()
        print(f"User ID from JWT: {user_id}")
        user = User.query.get(int(user_id))
        
        if not user:
            print(f"User not found for ID: {user_id}")
            return jsonify({'message': 'User not found'}), 404
        
        print(f"User found: {user.username}")
        return jsonify({'id': user.id, 'username': user.username}), 200
    except Exception as e:
        print(f"Error in get_current_user: {e}")
        return jsonify({'message': 'Internal server error'}), 500

# Todo相关API

# 获取所有Todo
@api_bp.route('/todos', methods=['GET'])
@jwt_required()
def get_todos():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': '用户不存在'}), 404  # 新增这行
    
    # 获取查询参数
    completed = request.args.get('completed')
    tag_id = request.args.get('tag_id')
    priority = request.args.get('priority')
    due_date = request.args.get('due_date')
    
    # 构建查询
    query = Todo.query.filter_by(user_id=user_id)
    
    # 过滤条件
    if completed is not None:
        query = query.filter_by(completed=completed.lower() == 'true')
    if tag_id:
        query = query.join(todo_tags).filter(todo_tags.c.tag_id == tag_id)
    if priority:
        query = query.filter_by(priority=priority)
    if due_date:
        # 查找指定日期的任务
        query_date = datetime.datetime.strptime(due_date, '%Y-%m-%d').date()
        query = query.filter(db.func.date(Todo.due_date) == query_date)
    
    todos = query.all()
    
    output = []
    for todo in todos:
        # 获取任务的标签
        tags = [{"id": tag.id, "name": tag.name, "color": tag.color} for tag in todo.tags]
        
        todo_data = {
            'id': todo.id,
            'title': todo.title,
            'description': todo.description,
            'completed': todo.completed,
            'created_at': todo.created_at.isoformat(),
            'due_date': todo.due_date.isoformat() if todo.due_date else None,
            'priority': todo.priority,
            'tags': tags
        }
        output.append(todo_data)
    
    return jsonify({'todos': output}), 200

# 创建新Todo
@api_bp.route('/todos', methods=['POST'])
@jwt_required()
def create_todo():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': '用户不存在'}), 404  # 新增这行
    data = request.get_json()
    
    # 处理截止日期
    due_date = None
    if data.get('due_date'):
        due_date = datetime.datetime.fromisoformat(data['due_date'])
    
    new_todo = Todo(
        title=data['title'],
        description=data.get('description'),
        completed=data.get('completed', False),
        due_date=due_date,
        priority=data.get('priority', 1),
        user_id=user_id
    )
    
    # 处理标签
    if data.get('tags'):
        for tag_id in data['tags']:
            tag = Tag.query.filter_by(id=tag_id, user_id=user_id).first()
            if tag:
                new_todo.tags.append(tag)
    
    db.session.add(new_todo)
    db.session.commit()
    
    # 获取任务的标签
    tags = [{"id": tag.id, "name": tag.name, "color": tag.color} for tag in new_todo.tags]
    
    return jsonify({
        'id': new_todo.id,
        'title': new_todo.title,
        'description': new_todo.description,
        'completed': new_todo.completed,
        'created_at': new_todo.created_at.isoformat(),
        'due_date': new_todo.due_date.isoformat() if new_todo.due_date else None,
        'priority': new_todo.priority,
        'tags': tags
    }), 201

# 更新Todo
@api_bp.route('/todos/<int:todo_id>', methods=['PUT'])
@jwt_required()
def update_todo(todo_id):
    user_id = get_jwt_identity()
    todo = Todo.query.filter_by(id=todo_id, user_id=user_id).first()
    
    if not todo:
        return jsonify({'message': 'Todo not found'}), 404
    
    data = request.get_json()
    
    if 'title' in data:
        todo.title = data['title']
    if 'description' in data:
        todo.description = data['description']
    if 'completed' in data:
        todo.completed = data['completed']
    if 'due_date' in data:
        todo.due_date = datetime.datetime.fromisoformat(data['due_date']) if data['due_date'] else None
    if 'priority' in data:
        todo.priority = data['priority']
    
    # 处理标签
    if 'tags' in data:
        # 先清除所有标签关联
        todo.tags.clear()
        # 添加新的标签关联
        for tag_id in data['tags']:
            tag = Tag.query.filter_by(id=tag_id, user_id=user_id).first()
            if tag:
                todo.tags.append(tag)
    
    db.session.commit()
    
    # 获取任务的标签
    tags = [{"id": tag.id, "name": tag.name, "color": tag.color} for tag in todo.tags]
    
    return jsonify({
        'id': todo.id,
        'title': todo.title,
        'description': todo.description,
        'completed': todo.completed,
        'created_at': todo.created_at.isoformat(),
        'due_date': todo.due_date.isoformat() if todo.due_date else None,
        'priority': todo.priority,
        'tags': tags
    }), 200

# 删除Todo
@api_bp.route('/todos/<int:todo_id>', methods=['DELETE'])
@jwt_required()
def delete_todo(todo_id):
    user_id = get_jwt_identity()
    todo = Todo.query.filter_by(id=todo_id, user_id=user_id).first()
    
    if not todo:
        return jsonify({'message': 'Todo not found'}), 404
    
    db.session.delete(todo)
    db.session.commit()
    
    return jsonify({'message': 'Todo deleted successfully'}), 200

# 标记Todo完成/未完成
@api_bp.route('/todos/<int:todo_id>/toggle', methods=['PUT'])
@jwt_required()
def toggle_todo(todo_id):
    user_id = get_jwt_identity()
    todo = Todo.query.filter_by(id=todo_id, user_id=user_id).first()
    
    if not todo:
        return jsonify({'message': 'Todo not found'}), 404
    
    todo.completed = not todo.completed
    db.session.commit()
    
    # 获取任务的标签
    tags = [{"id": tag.id, "name": tag.name, "color": tag.color} for tag in todo.tags]
    
    return jsonify({
        'id': todo.id,
        'title': todo.title,
        'description': todo.description,
        'completed': todo.completed,
        'created_at': todo.created_at.isoformat(),
        'due_date': todo.due_date.isoformat() if todo.due_date else None,
        'priority': todo.priority,
        'tags': tags
    }), 200

# 标签相关API

# 获取所有标签
@api_bp.route('/tags', methods=['GET'])
@jwt_required()
def get_tags():
    user_id = get_jwt_identity()
    tags = Tag.query.filter_by(user_id=user_id).all()
    
    output = []
    for tag in tags:
        tag_data = {
            'id': tag.id,
            'name': tag.name,
            'color': tag.color
        }
        output.append(tag_data)
    
    return jsonify({'tags': output}), 200

# 创建新标签
@api_bp.route('/tags', methods=['POST'])
@jwt_required()
def create_tag():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    new_tag = Tag(
        name=data['name'],
        color=data.get('color', '#3498db'),
        user_id=user_id
    )
    
    db.session.add(new_tag)
    db.session.commit()
    
    return jsonify({
        'id': new_tag.id,
        'name': new_tag.name,
        'color': new_tag.color
    }), 201

# 更新标签
@api_bp.route('/tags/<int:tag_id>', methods=['PUT'])
@jwt_required()
def update_tag(tag_id):
    user_id = get_jwt_identity()
    tag = Tag.query.filter_by(id=tag_id, user_id=user_id).first()
    
    if not tag:
        return jsonify({'message': 'Tag not found'}), 404
    
    data = request.get_json()
    
    if 'name' in data:
        tag.name = data['name']
    if 'color' in data:
        tag.color = data['color']
    
    db.session.commit()
    
    return jsonify({
        'id': tag.id,
        'name': tag.name,
        'color': tag.color
    }), 200

# 删除标签
@api_bp.route('/tags/<int:tag_id>', methods=['DELETE'])
@jwt_required()
def delete_tag(tag_id):
    user_id = get_jwt_identity()
    tag = Tag.query.filter_by(id=tag_id, user_id=user_id).first()
    
    if not tag:
        return jsonify({'message': 'Tag not found'}), 404
    
    db.session.delete(tag)
    db.session.commit()
    
    return jsonify({'message': 'Tag deleted successfully'}), 200