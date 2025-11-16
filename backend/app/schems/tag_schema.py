from marshmallow import Schema, fields, validate
import re

class TagSchema(Schema):
    """
    标签数据验证模式
    """
    id = fields.Int(dump_only=True)
    name = fields.Str(
        required=True,
        validate=[
            validate.Length(min=1, max=50, error="标签名称长度必须在1到50个字符之间"),
            validate.Regexp(r'^[a-zA-Z0-9_\u4e00-\u9fa5]+$', error="标签名称只能包含字母、数字、下划线和中文")
        ]
    )
    color = fields.Str(
        validate=[
            validate.Regexp(r'^#[0-9A-Fa-f]{6}$', error="颜色格式无效，请使用十六进制颜色值（如：#FF0000）")
        ]
    )
    created_at = fields.DateTime(dump_only=True)

class TagResponseSchema(Schema):
    """
    标签响应数据模式
    """
    id = fields.Int()
    name = fields.Str()
    color = fields.Str()
    created_at = fields.DateTime()

class TagUpdateSchema(Schema):
    """
    标签更新数据验证模式
    """
    name = fields.Str(
        validate=[
            validate.Length(min=1, max=50, error="标签名称长度必须在1到50个字符之间"),
            validate.Regexp(r'^[a-zA-Z0-9_\u4e00-\u9fa5]+$', error="标签名称只能包含字母、数字、下划线和中文")
        ]
    )
    color = fields.Str(
        validate=[
            validate.Regexp(r'^#[0-9A-Fa-f]{6}$', error="颜色格式无效，请使用十六进制颜色值（如：#FF0000）")
        ]
    )