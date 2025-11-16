from pathlib import Path

from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from flask_migrate import Migrate

from backend.app.config import Config

# 创建数据库实例
db = SQLAlchemy()
# 创建CORS实例
cors = CORS()
# 创建Bcrypt实例用于密码哈希
bcrypt = Bcrypt()
# 创建JWT实例
jwt = JWTManager()
# 创建SocketIO实例
socketio = SocketIO()
# 创建Migrate实例
migrate = Migrate()
# 前端目录路径
FRONTEND_DIR = Path(__file__).parent.parent.parent / "frontend"
def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 初始化扩展
    db.init_app(app)
    # 配置CORS以允许所有来源
    cors.init_app(app, resources={"*": {"origins": "*"}})
    bcrypt.init_app(app)
    jwt.init_app(app)
    # 初始化SocketIO
    socketio.init_app(app, cors_allowed_origins="*")
    # 初始化Migrate
    migrate.init_app(app, db)
    
    # 添加安全头
    @app.after_request
    def add_security_headers(response):
        # 防止浏览器对响应的内容类型进行嗅探
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response
    #托管前端页面的路由
    @app.route('/')
    def index():
        return send_from_directory(FRONTEND_DIR, 'index.html')

    @app.route('/todos.html')
    def todos():
        return send_from_directory(FRONTEND_DIR, 'todos.html')

    #处理前端静态文件
    @app.route('/<path:filename>')
    def static_files(filename):
        return send_from_directory(FRONTEND_DIR, filename)


    # 注册蓝图
    from backend.app.api.routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # 导入并初始化提醒服务
    from backend.app.services.reminder_service import init_reminder_service
    init_reminder_service(app)
    
    return app