from backend.app import db
from backend.app.models.models import Tag, Todo, todo_tags
from backend.app.schems import TagSchema, TagUpdateSchema
from marshmallow import ValidationError

def get_tags(user_id):
    """
    获取用户的所有标签
    """
    tags = Tag.query.filter_by(user_id=user_id).all()
    
    # 转换为响应格式
    output = []
    for tag in tags:
        output.append({
            'id': tag.id,
            'name': tag.name,
            'color': tag.color
        })
    
    return output

def create_tag(user_id, name, color=None):
    """
    创建新标签
    """
    # 使用schema验证输入数据
    tag_schema = TagSchema()
    try:
        # 验证数据
        tag_data = tag_schema.load({
            'name': name,
            'color': color
        })
    except ValidationError as err:
        raise ValueError(err.messages)
    
    # 解析验证后的数据
    name = tag_data['name']
    color = tag_data.get('color', '#3498db')  # 默认颜色
    
    new_tag = Tag(
        name=name,
        color=color,
        user_id=user_id
    )
    
    db.session.add(new_tag)
    db.session.commit()
    
    return {
        'id': new_tag.id,
        'name': new_tag.name,
        'color': new_tag.color
    }

def update_tag(user_id, tag_id, name=None, color=None):
    """
    更新标签
    """
    tag = Tag.query.filter_by(id=tag_id, user_id=user_id).first()
    
    if not tag:
        raise ValueError('Tag not found')
    
    # 准备更新数据
    update_data = {}
    if name is not None:
        update_data['name'] = name
    if color is not None:
        update_data['color'] = color
    
    # 使用schema验证更新数据
    tag_update_schema = TagUpdateSchema()
    try:
        # 验证数据
        validated_data = tag_update_schema.load(update_data)
    except ValidationError as err:
        raise ValueError(err.messages)
    
    # 应用更新
    if 'name' in validated_data:
        tag.name = validated_data['name']
    if 'color' in validated_data:
        tag.color = validated_data['color']
    
    db.session.commit()
    
    return {
        'id': tag.id,
        'name': tag.name,
        'color': tag.color
    }

def delete_tag(user_id, tag_id):
    """
    删除标签
    """
    tag = Tag.query.filter_by(id=tag_id, user_id=user_id).first()
    
    if not tag:
        raise ValueError('Tag not found')
    
    # 先删除标签与任务的关联
    db.session.execute(todo_tags.delete().where(todo_tags.c.tag_id == tag_id))
    
    # 删除标签
    db.session.delete(tag)
    db.session.commit()
    
    return {'message': 'Tag deleted successfully'}

def get_tag_todos(user_id, tag_id):
    """
    获取特定标签的所有任务
    """
    tag = Tag.query.filter_by(id=tag_id, user_id=user_id).first()
    
    if not tag:
        raise ValueError('Tag not found')
    
    todos = tag.todos.all()
    
    # 转换为响应格式
    output = []
    for todo in todos:
        tags = [{'id': t.id, 'name': t.name, 'color': t.color} for t in todo.tags]
        
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