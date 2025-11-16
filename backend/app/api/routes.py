from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import datetime

from backend.app.services.user_service import get_user_by_id, create_user, authenticate_user
from backend.app.services.todo_service import (
    get_todos, get_today_todos, get_todos_preview, create_todo, update_todo, delete_todo,
    get_week_todos, get_upcoming_todos, get_overdue_todos, toggle_todo_completion
)
from backend.app.services.tag_service import get_tags, create_tag, update_tag, delete_tag, get_tag_todos

# 创建蓝图
api_bp = Blueprint('api', __name__)

# 注册路由
@api_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    try:
        create_user(data['username'], data['password'])
        return jsonify({'message': 'User created successfully'}), 201
    except ValueError as e:
        return jsonify({'message': str(e)}), 400

# 登录路由
@api_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # 验证用户身份
    user = authenticate_user(data['username'], data['password'])
    
    if not user:
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
        user = get_user_by_id(int(user_id))
        
        if not user:
            print(f"User not found for ID: {user_id}")
            return jsonify({'message': 'User not found'}), 404
        
        print(f"User found: {user.username}")
        return jsonify({'id': user.id, 'username': user.username}), 200
    except Exception as e:
        print(f"Error in get_current_user: {e}")
        return jsonify({'message': 'Internal server error'}), 500

# Todo相关API

# 获取所有Todo (支持过滤、搜索和排序)
@api_bp.route('/todos', methods=['GET'])
@jwt_required()
def api_get_todos():
    user_id = get_jwt_identity()
    
    # 获取查询参数
    completed = request.args.get('completed')
    tag_id = request.args.get('tag_id')
    priority = request.args.get('priority')
    due_date = request.args.get('due_date')
    search = request.args.get('search')
    sort_by = request.args.get('sort_by')
    sort_order = request.args.get('sort_order', 'asc')
    
    todos = get_todos(user_id, completed, tag_id, priority, due_date, search, sort_by, sort_order)
    
    return jsonify({'todos': todos}), 200

# 获取今日待办事项
@api_bp.route('/todos/today', methods=['GET'])
@jwt_required()
def api_get_today_todos():
    user_id = get_jwt_identity()
    
    todos = get_today_todos(user_id)
    
    return jsonify({'todos': todos}), 200

# 获取任务预览统计数据
@api_bp.route('/todos/preview', methods=['GET'])
@jwt_required()
def api_get_todos_preview():
    user_id = get_jwt_identity()
    
    preview_data = get_todos_preview(user_id)
    
    return jsonify(preview_data), 200

# 获取指定起始日期的七天任务
@api_bp.route('/todos/week', methods=['GET'])
@jwt_required()
def api_get_week_todos():
    user_id = get_jwt_identity()
    
    # 获取查询参数，默认使用今天
    start_date_param = request.args.get('start_date')
    
    preview_data = get_todos_preview(user_id, start_date_param)
    
    return jsonify(preview_data), 200

# 创建新Todo
@api_bp.route('/todos', methods=['POST'])
@jwt_required()
def api_create_todo():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    try:
        new_todo = create_todo(
            user_id,
            data['title'],
            data.get('description'),
            data.get('completed', False),
            data.get('due_date'),
            data.get('priority', 1),
            data.get('tags')
        )
        return jsonify(new_todo), 201
    except ValueError as e:
        return jsonify({'message': str(e)}), 400

# 更新Todo
@api_bp.route('/todos/<int:todo_id>', methods=['PUT'])
@jwt_required()
def api_update_todo(todo_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    
    try:
        updated_todo = update_todo(
            user_id,
            todo_id,
            data.get('title'),
            data.get('description'),
            data.get('completed'),
            data.get('due_date'),
            data.get('priority'),
            data.get('tags')
        )
        return jsonify(updated_todo), 200
    except ValueError as e:
        return jsonify({'message': str(e)}), 404
    
# 删除Todo
@api_bp.route('/todos/<int:todo_id>', methods=['DELETE'])
@jwt_required()
def api_delete_todo(todo_id):
    user_id = get_jwt_identity()
    
    try:
        result = delete_todo(user_id, todo_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'message': str(e)}), 404

# 标记Todo完成/未完成
@api_bp.route('/todos/<int:todo_id>/toggle', methods=['PUT'])
@jwt_required()
def api_toggle_todo(todo_id):
    user_id = get_jwt_identity()
    
    try:
        result = toggle_todo_completion(user_id, todo_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'message': str(e)}), 404

# 标签相关API

# 获取所有标签
@api_bp.route('/tags', methods=['GET'])
@jwt_required()
def api_get_tags():
    user_id = get_jwt_identity()
    tags = get_tags(user_id)
    return jsonify({'tags': tags}), 200

# 创建新标签
@api_bp.route('/tags', methods=['POST'])
@jwt_required()
def api_create_tag():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    new_tag = create_tag(user_id, data['name'], data.get('color'))
    return jsonify(new_tag), 201

# 更新标签
@api_bp.route('/tags/<int:tag_id>', methods=['PUT'])
@jwt_required()
def api_update_tag(tag_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    
    try:
        updated_tag = update_tag(user_id, tag_id, data.get('name'), data.get('color'))
        return jsonify(updated_tag), 200
    except ValueError as e:
        return jsonify({'message': str(e)}), 404

# 删除标签
@api_bp.route('/tags/<int:tag_id>', methods=['DELETE'])
@jwt_required()
def api_delete_tag(tag_id):
    user_id = get_jwt_identity()
    
    try:
        result = delete_tag(user_id, tag_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'message': str(e)}), 404

# 获取即将到期的任务
@api_bp.route('/todos/upcoming', methods=['GET'])
@jwt_required()
def api_get_upcoming_todos():
    user_id = get_jwt_identity()
    minutes = request.args.get('minutes', 60, type=int)
    
    todos = get_upcoming_todos(user_id, minutes)
    
    return jsonify({'todos': todos}), 200