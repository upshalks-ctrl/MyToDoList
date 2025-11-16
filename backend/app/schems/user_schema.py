from marshmallow import Schema, fields, validate

class UserSchema(Schema):
    """
    用户数据验证模式
    """
    id = fields.Int(dump_only=True)  # 只用于输出，不用于输入验证
    username = fields.Str(
        required=True,
        validate=[
            validate.Length(min=3, max=50, error="用户名长度必须在3到50个字符之间"),
            validate.Regexp(r'^[a-zA-Z0-9_]+$', error="用户名只能包含字母、数字和下划线")
        ]
    )
    password = fields.Str(
        required=True,
        load_only=True,  # 只用于输入，不用于输出
        validate=[
            validate.Length(min=6, error="密码长度至少为6个字符"),
            validate.Regexp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)', 
                        error="密码必须包含至少一个大写字母、一个小写字母和一个数字")
        ]
    )
    created_at = fields.DateTime(dump_only=True)

class UserLoginSchema(Schema):
    """
    用户登录数据验证模式
    """
    username = fields.Str(required=True, validate=validate.Length(min=3, max=50))
    password = fields.Str(required=True, validate=validate.Length(min=6))

class UserResponseSchema(Schema):
    """
    用户响应数据模式
    """
    id = fields.Int()
    username = fields.Str()
    created_at = fields.DateTime()