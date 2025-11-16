from datetime import datetime, timedelta, timezone
from backend.app import db
from backend.app.models.models import Todo, Tag
from backend.app.schems import TodoSchema, TodoUpdateSchema
from marshmallow import ValidationError

def get_todos(user_id, completed=None, tag_id=None, priority=None, due_date=None, search=None, sort_by=None, sort_order=None):
    """
    获取用户的待办事项列表，支持过滤和搜索
    """
    # 构建查询
    query = Todo.query.filter_by(user_id=user_id)
    
    # 过滤条件
    if completed is not None:
        query = query.filter_by(completed=completed.lower() == 'true')
    if tag_id:
        query = query.join(Todo.tags).filter(Tag.id == tag_id)
    if priority:
        query = query.filter_by(priority=priority)
    if due_date:
        # 查找指定日期的任务
        query_date = datetime.strptime(due_date, '%Y-%m-%d').date()
        query = query.filter(db.func.date(Todo.due_date) == query_date)
    if search:
        # 搜索任务标题和描述
        search_term = f"%{search}%"
        query = query.filter(
            db.or_(
                Todo.title.ilike(search_term),
                Todo.description.ilike(search_term)
            )
        )
    
    # 排序条件
    if sort_by and sort_by != 'tags':
        if sort_by == 'due_date':
            if sort_order == 'desc':
                query = query.order_by(Todo.due_date.desc())
            else:
                query = query.order_by(Todo.due_date.asc())
        elif sort_by == 'priority':
            if sort_order == 'desc':
                query = query.order_by(Todo.priority.desc())
            else:
                query = query.order_by(Todo.priority.asc())
        elif sort_by == 'created_at':
            if sort_order == 'desc':
                query = query.order_by(Todo.created_at.desc())
            else:
                query = query.order_by(Todo.created_at.asc())
        elif sort_by == 'title':
            if sort_order == 'desc':
                query = query.order_by(Todo.title.desc())
            else:
                query = query.order_by(Todo.title.asc())
    
    todos = query.all()
    
    # 按标签排序需要特殊处理
    if sort_by == 'tags':
        def get_first_tag_name(todo):
            """
            获取任务的第一个标签名称，如果没有标签则返回空字符串
            """
            tags = list(todo.tags)
            if tags:
                return tags[0].name
            return ""
        
        # 按标签名称排序
        todos.sort(key=get_first_tag_name, reverse=(sort_order == 'desc'))
    
    # 转换为响应格式
    output = []
    for todo in todos:
        tags = [{'id': tag.id, 'name': tag.name, 'color': tag.color} for tag in todo.tags]
        
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
    
    return output

def get_today_todos(user_id):
    """
    获取用户今天的待办事项
    """
    # 获取今天的日期
    today = datetime.now(timezone.utc).date()
    
    # 构建查询
    query = Todo.query.filter_by(user_id=user_id)
    query = query.filter(db.func.date(Todo.due_date) == today)
    query = query.order_by(Todo.due_date.asc())  # 按时间顺序排序
    
    todos = query.all()
    
    # 转换为响应格式
    output = []
    for todo in todos:
        tags = [{'id': tag.id, 'name': tag.name, 'color': tag.color} for tag in todo.tags]
        
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
    
    return output

def get_week_todos(user_id):
    """
    获取用户本周的待办事项
    """
    # 获取今天的日期
    today = datetime.now(timezone.utc).date()
    # 计算本周一和下周一的日期
    monday = today - timedelta(days=today.weekday())
    next_monday = monday + timedelta(days=7)
    
    # 构建查询
    query = Todo.query.filter_by(user_id=user_id)
    query = query.filter(db.func.date(Todo.due_date) >= monday)
    query = query.filter(db.func.date(Todo.due_date) < next_monday)
    query = query.order_by(Todo.due_date.asc())  # 按时间顺序排序
    
    todos = query.all()
    
    # 按日期分组
    week_todos = {}
    for todo in todos:
        date_str = todo.due_date.strftime('%Y-%m-%d')
        if date_str not in week_todos:
            week_todos[date_str] = []
        
        tags = [{'id': tag.id, 'name': tag.name, 'color': tag.color} for tag in todo.tags]
        
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
        week_todos[date_str].append(todo_data)
    
    return week_todos

def get_todos_preview(user_id, start_date_param=None):
    """
    获取一周任务预览数据，按日期分组
    """
    # 获取起始日期，如果没有提供则使用今天
    if start_date_param:
        try:
            # 解析起始日期参数
            start_date = datetime.strptime(start_date_param, '%Y-%m-%d').date()
        except ValueError:
            # 如果日期格式错误，使用今天
            start_date = datetime.now(timezone.utc).date()
    else:
        start_date = datetime.now(timezone.utc).date()
    
    # 统计数据
    total_tasks = Todo.query.filter_by(user_id=user_id).count()
    completed_tasks = Todo.query.filter_by(user_id=user_id, completed=True).count()
    pending_tasks = Todo.query.filter_by(user_id=user_id, completed=False).count()
    today_tasks = Todo.query.filter_by(user_id=user_id).filter(db.func.date(Todo.due_date) == datetime.now(timezone.utc).date()).count()
    
    # 获取指定起始日期后的7天任务数据
    week_tasks = []
    for i in range(7):
        date = start_date + timedelta(days=i)
        
        # 查询当天到期的任务
        tasks = Todo.query.filter_by(user_id=user_id)
        tasks = tasks.filter(db.func.date(Todo.due_date) == date)
        tasks = tasks.order_by(Todo.due_date.asc()).all()
        
        # 转换为响应格式
        task_list = []
        for task in tasks:
            task_list.append({
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'completed': task.completed,
                'due_date': task.due_date.isoformat() if task.due_date else None,
                'priority': task.priority,
                'tags': [{'id': tag.id, 'name': tag.name} for tag in task.tags]
            })
        
        # 添加当天数据
        week_tasks.append({
            'date': date.isoformat(),
            'formatted_date': date.strftime('%Y-%m-%d'),
            'day_name': date.strftime('%A'),
            'tasks': task_list,
            'task_count': len(task_list)
        })
    
    return {
        'stats': {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'pending_tasks': pending_tasks,
            'today_tasks': today_tasks
        },
        'week_tasks': week_tasks
    }

def create_todo(user_id, title, description=None, completed=False, due_date=None, priority=1, tags=None):
    """
    创建新的待办事项
    """
    # 使用schema验证输入数据
    todo_schema = TodoSchema()
    try:
        # 验证数据
        todo_data = todo_schema.load({
            'title': title,
            'description': description,
            'completed': completed,
            'due_date': due_date,
            'priority': priority,
            'tags': tags
        })
    except ValidationError as err:
        raise ValueError(err.messages)
    
    # 解析验证后的数据
    title = todo_data['title']
    description = todo_data.get('description')
    completed = todo_data.get('completed', False)
    due_date = todo_data.get('due_date')
    priority = todo_data.get('priority', 1)
    tags = todo_data.get('tags', [])
    
    new_todo = Todo(
        title=title,
        description=description,
        completed=completed,
        due_date=due_date,
        priority=priority,
        user_id=user_id
    )
    
    # 处理标签
    if tags:
        for tag_id in tags:
            tag = Tag.query.filter_by(id=tag_id, user_id=user_id).first()
            if tag:
                new_todo.tags.append(tag)
    
    db.session.add(new_todo)
    db.session.commit()
    
    # 转换为响应格式
    tags = [{'id': tag.id, 'name': tag.name, 'color': tag.color} for tag in new_todo.tags]
    
    return {
        'id': new_todo.id,
        'title': new_todo.title,
        'description': new_todo.description,
        'completed': new_todo.completed,
        'created_at': new_todo.created_at.isoformat(),
        'due_date': new_todo.due_date.isoformat() if new_todo.due_date else None,
        'priority': new_todo.priority,
        'tags': tags
    }

def update_todo(user_id, todo_id, title=None, description=None, completed=None, due_date=None, priority=None, tags=None):
    """
    更新待办事项
    """
    todo = Todo.query.filter_by(id=todo_id, user_id=user_id).first()
    
    if not todo:
        raise ValueError('Todo not found')
    
    # 准备更新数据
    update_data = {}
    if title is not None:
        update_data['title'] = title
    if description is not None:
        update_data['description'] = description
    if completed is not None:
        update_data['completed'] = completed
    if due_date is not None:
        update_data['due_date'] = due_date
    if priority is not None:
        update_data['priority'] = priority
    if tags is not None:
        update_data['tags'] = tags
    
    # 使用schema验证更新数据
    todo_update_schema = TodoUpdateSchema()
    try:
        # 验证数据
        validated_data = todo_update_schema.load(update_data)
    except ValidationError as err:
        raise ValueError(err.messages)
    
    # 应用更新
    if 'title' in validated_data:
        todo.title = validated_data['title']
    if 'description' in validated_data:
        todo.description = validated_data['description']
    if 'completed' in validated_data:
        todo.completed = validated_data['completed']
        if validated_data['completed']:
            # 当任务标记为完成时，设置completed_at为当前时间
            from datetime import datetime, timezone
            todo.completed_at = datetime.now(timezone.utc)
    if 'due_date' in validated_data:
        todo.due_date = validated_data['due_date']
    if 'priority' in validated_data:
        todo.priority = validated_data['priority']
    if 'tags' in validated_data:
        # 先清除所有标签关联
        todo.tags.clear()
        # 添加新的标签关联
        for tag_id in validated_data['tags']:
            tag = Tag.query.filter_by(id=tag_id, user_id=user_id).first()
            if tag:
                todo.tags.append(tag)
    
    db.session.commit()
    
    # 转换为响应格式
    tags = [{'id': tag.id, 'name': tag.name, 'color': tag.color} for tag in todo.tags]
    
    return {
        'id': todo.id,
        'title': todo.title,
        'description': todo.description,
        'completed': todo.completed,
        'created_at': todo.created_at.isoformat(),
        'due_date': todo.due_date.isoformat() if todo.due_date else None,
        'priority': todo.priority,
        'tags': tags
    }

def delete_todo(user_id, todo_id):
    """
    删除待办事项
    """
    todo = Todo.query.filter_by(id=todo_id, user_id=user_id).first()
    
    if not todo:
        raise ValueError('Todo not found')
    
    db.session.delete(todo)
    db.session.commit()
    
    return {'message': 'Todo deleted successfully'}

def get_overdue_todos(user_id):
    """
    获取过期的待办事项
    """
    now = datetime.now(timezone.utc)
    
    query = Todo.query.filter_by(user_id=user_id, completed=False)
    query = query.filter(Todo.due_date < now)
    
    todos = query.all()
    
    # 转换为响应格式
    output = []
    for todo in todos:
        tags = [{'id': tag.id, 'name': tag.name, 'color': tag.color} for tag in todo.tags]
        
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
    
    return output

def toggle_todo_completion(user_id, todo_id):
    """
    切换待办事项的完成状态
    """
    todo = Todo.query.filter_by(id=todo_id, user_id=user_id).first()
    
    if not todo:
        raise ValueError('Todo not found')
    
    todo.completed = not todo.completed
    db.session.commit()
    
    # 转换为响应格式
    tags = [{'id': tag.id, 'name': tag.name, 'color': tag.color} for tag in todo.tags]
    
    return {
        'id': todo.id,
        'title': todo.title,
        'description': todo.description,
        'completed': todo.completed,
        'created_at': todo.created_at.isoformat(),
        'due_date': todo.due_date.isoformat() if todo.due_date else None,
        'priority': todo.priority,
        'tags': tags
    }

def get_upcoming_todos(user_id, minutes=60):
    """
    获取即将到期的待办事项（默认60分钟内）
    """
    now = datetime.now(timezone.utc)
    upcoming = now + timedelta(minutes=minutes)
    
    query = Todo.query.filter_by(user_id=user_id, completed=False)
    query = query.filter(Todo.due_date >= now)
    query = query.filter(Todo.due_date <= upcoming)
    
    todos = query.all()
    
    # 转换为响应格式
    output = []
    for todo in todos:
        tags = [{'id': tag.id, 'name': tag.name, 'color': tag.color} for tag in todo.tags]
        
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
    
    return output

def delete_old_completed_tasks(user_id):
    """
    删除用户24小时前已完成的任务
    """
    now = datetime.now(timezone.utc)
    twenty_four_hours_ago = now - timedelta(hours=24)
    
    # 查询用户所有已完成且完成时间超过24小时的任务
    # 注意：由于Todo模型中没有completed_at字段，我们假设任务是在创建后立即完成的
    # 实际应用中，应该添加一个completed_at字段来记录任务完成的时间
    old_tasks = Todo.query.filter_by(user_id=user_id, completed=True)
    old_tasks = old_tasks.filter(Todo.created_at < twenty_four_hours_ago)
    
    # 删除这些任务
    deleted_count = old_tasks.delete()
    db.session.commit()
    
    return deleted_count