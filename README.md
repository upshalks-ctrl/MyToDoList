# Todo List

一个基于Flask和前端原生技术栈的个人任务管理应用，支持用户注册登录、任务创建与管理、标签分类、优先级设置等功能。

## 功能特点

- 用户认证：注册、登录功能（基于JWT实现身份验证）
- 任务管理：创建、查看、筛选待办事项
- 任务属性：支持设置截止日期、优先级（低/中/高）、标签分类
- 标签管理：自定义标签及颜色，便于任务分类
- 响应式设计：适配不同屏幕尺寸

## 技术栈

### 后端
- Python 3.x
- Flask：Web应用框架
- Flask-SQLAlchemy：ORM数据库操作
- Flask-JWT-Extended：JWT身份认证
- Flask-CORS：处理跨域请求
- Flask-Bcrypt：密码加密
- MySQL：数据库存储

### 前端
- HTML5/CSS3
- JavaScript（原生）
- Tailwind CSS：样式框架
- Font Awesome：图标库

## 项目结构

```
mytodolist/
├── backend/                  # 后端代码
│   ├── app/
│   │   ├── __init__.py       # 应用初始化
│   │   ├── api/
│   │   │   └── routes.py     # API路由
│   │   └── models/
│   │       └── models.py     # 数据模型
│   └── run.py                # 应用启动入口
├── frontend/                 # 前端静态文件
│   ├── index.html            # 登录/注册页面
│   ├── todos.html            # 任务管理页面
│   └── test.html             # 测试页面
├── requirements.txt          # 依赖列表
├── TESTING_GUIDE.md          # 测试指南
└── FINAL_FIXES.md            # 修复记录
```

## 安装与部署

### 前置条件
- Python 3.x
- MySQL 数据库
- pip（Python包管理工具）

### 步骤

1. **克隆仓库**
   ```bash
   git clone <仓库地址>
   cd mytodolist
   ```

2. **创建虚拟环境并激活**
   ```bash
   # 创建虚拟环境
   python -m venv venv
   
   # 激活虚拟环境
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **配置环境变量**
   创建`.env`文件，添加以下配置：
   ```
   SECRET_KEY=your_secret_key
   JWT_SECRET_KEY=your_jwt_secret_key  # 需与SECRET_KEY保持一致
   SQLALCHEMY_DATABASE_URI=mysql+mysqlconnector://username:password@localhost/db_name
   ```

5. **初始化数据库**
   ```bash
   # 启动Python交互环境
   python
   
   # 在Python环境中执行
   from backend.app import create_app, db
   app = create_app()
   with app.app_context():
       db.create_all()
   exit()
   ```

6. **启动应用**
   ```bash
   python backend/run.py
   ```

7. **访问应用**
   打开浏览器，访问 `http://127.0.0.1:5000` 即可进入登录页面

## 使用说明

1. **注册/登录**：首次使用需注册账号，已有账号直接登录
2. **添加任务**：点击"添加任务"，填写任务标题、描述、截止日期、优先级及标签
3. **管理任务**：在任务列表中可查看、勾选完成状态
4. **标签管理**：通过"管理标签"功能创建自定义标签，用于任务分类
5. **筛选任务**：可按日期、优先级、标签等条件筛选任务


