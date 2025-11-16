from marshmallow import Schema, fields, validate, validates, ValidationError
from datetime import datetime, timezone

class TodoSchema(Schema):
    """
    待办事项数据验证模式
    """
    id = fields.Int(dump_only=True)
    title = fields.Str(
        required=True,
        validate=[
            validate.Length(min=1, max=200, error="标题长度必须在1到200个字符之间")
        ]
    )
    description = fields.Str(
        validate=validate.Length(max=1000, error="描述长度不能超过1000个字符")
    )
    completed = fields.Boolean(load_default=False)
    created_at = fields.DateTime(dump_only=True)
    due_date = fields.DateTime(
        validate=[
            lambda value: value > datetime.now(timezone.utc) if value else True
        ],
        error_messages={
            'invalid': '截止日期格式无效，请使用ISO格式（如：2023-12-31T23:59:59）',
            'validator_failed': '截止日期不能早于当前时间'
        }
    )
    priority = fields.Int(
        validate=validate.OneOf([1, 2, 3], error="优先级必须是1（低）、2（中）或3（高）")
    )
    tags = fields.List(fields.Int(), load_only=True, validate=validate.Length(max=5, error="最多只能添加5个标签"))



class TodoResponseSchema(Schema):
    """
    待办事项响应数据模式
    """
    id = fields.Int()
    title = fields.Str()
    description = fields.Str()
    completed = fields.Boolean()
    created_at = fields.DateTime()
    due_date = fields.DateTime()
    priority = fields.Str()
    tags = fields.List(fields.Dict())

class TodoUpdateSchema(Schema):
    """
    待办事项更新数据验证模式
    """
    title = fields.Str(
        validate=[
            validate.Length(min=1, max=200, error="标题长度必须在1到200个字符之间")
        ]
    )
    description = fields.Str(
        validate=validate.Length(max=1000, error="描述长度不能超过1000个字符")
    )
    completed = fields.Boolean()
    due_date = fields.DateTime(
        error_messages={
            'invalid': '截止日期格式无效，请使用ISO格式（如：2023-12-31T23:59:59）'
        }
    )
    priority = fields.Int(
        validate=validate.OneOf([1, 2, 3], error="优先级必须是1（低）、2（中）或3（高）")
    )
    tags = fields.List(fields.Int(), validate=validate.Length(max=5, error="最多只能添加5个标签"))

class TodoFilterSchema(Schema):
    """
    待办事项过滤和排序参数验证模式
    """
    search = fields.Str(validate=validate.Length(max=100, error="搜索关键词长度不能超过100个字符"))
    priority = fields.Int(validate=validate.OneOf([1, 2, 3], error="优先级必须是1（低）、2（中）或3（高）"))
    completed = fields.Boolean()
    sort_by = fields.Str(validate=validate.OneOf(['due_date', 'priority', 'title'], error="排序字段必须是due_date、priority或title"))
    sort_order = fields.Str(validate=validate.OneOf(['asc', 'desc'], error="排序顺序必须是asc或desc"))