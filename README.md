# Todo List 项目说明文档

## 1. 技术选型

- **编程语言**：
  - 后端：Python 3.x，理由：语法简洁，适合快速开发后端API，拥有丰富的Web框架生态
  - 前端：JavaScript（原生），理由：无需额外学习框架，直接操作DOM，适合中小型应用

- **框架/库**：
  - 后端：Flask，理由：轻量级Web框架，易于扩展，适合构建RESTful API
  - 前端：Tailwind CSS，理由：实用优先的CSS框架，加速UI开发；Font Awesome，提供丰富的图标支持
  - 身份认证：Flask-JWT-Extended，理由：专为Flask设计的JWT认证扩展，易于集成

- **数据库/存储**：
  - MySQL，理由：关系型数据库，适合存储结构化的任务和用户数据，支持复杂查询
  - SQLAlchemy，理由：强大的ORM工具，简化数据库操作，提高代码可读性

- **替代方案对比**：
  - 未使用Django：Django功能全面但相对重量级，对于本项目来说Flask的轻量特性更合适
  - 未使用MongoDB：任务数据具有明确的关系结构（用户-任务-标签），关系型数据库更适合
  - 未使用React/Vue：项目规模适中，原生JavaScript已足够满足需求，减少学习和维护成本

## 2. 项目结构设计

- 整体架构采用前后端分离模式：
  - 后端：基于Flask的RESTful API服务，处理业务逻辑和数据存储
  - 前端：静态HTML页面，通过JavaScript与后端API交互
  - 数据库：MySQL存储用户、任务和标签数据

- 目录结构：

```
mytodolist/
├── backend/                  # 后端代码
│   ├── app/
│   │   ├── __init__.py       # 应用初始化
│   │   ├── api/
│   │   │   └── routes.py     # API路由定义
│   │   ├── models/
│   │   │   └── models.py     # 数据模型定义
│   │   ├── schems/
│   │   │   └── todo_schema.py # 数据验证模式
│   │   └── services/
│   │       └── todo_service.py # 业务逻辑处理
│   └── run.py                # 应用启动入口
├── frontend/                 # 前端静态文件
│   ├── index.html            # 登录/注册页面
│   ├── todos.html            # 任务管理页面
│   ├── css/
│   │   └── style.css         # 样式文件
│   └── js/
│       └── app.js            # 前端交互逻辑
├── requirements.txt          # 依赖列表

```

- 模块职责说明：
  - `backend/app/api/routes.py`：定义API端点和请求处理逻辑
  - `backend/app/models/models.py`：定义数据库模型
  - `backend/app/schems/`：数据验证和序列化
  - `backend/app/services/`：实现核心业务逻辑
  - `frontend/js/app.js`：处理前端交互、API调用和页面渲染
  - `frontend/*.html`：页面结构和UI组件

## 3. 需求细节与决策

- 任务属性要求：
  - 标题：必填项，长度限制1-200字符
  - 描述：可选，最长1000字符
  - 截止日期：必填，必须晚于当前时间
  - 优先级：必选，分为低(1)、中(2)、高(3)三个等级
  - 标签：可选，最多可添加5个标签

- 任务状态展示：
  - 已完成任务通过勾选框标记
  - 界面上可能通过样式区分

- 任务排序与筛选：
  - 默认按创建时间排序
  - 支持按截止日期、优先级、标签进行筛选
  - 提供搜索功能快速定位任务

- 实时提醒：
  - 在截止时间前一个小时，十五分钟，五分钟提醒，然后通过点击任务查看任务详情
  - WebSocket 服务器 ：使用 Flask-SocketIO 等库与后端框架集成
  - 定时任务/事件触发器 ：单独创建一个线程负责检测需要发送提醒的事件（如待办事项到期）
  - 用户连接管理 ：维护用户 ID 与 WebSocket 连接的映射关系

## 4. AI 使用说明

- 负责前端框架的编写
- 负责初始项目架构的编写，通过ai设计一个初始项目架构，在使用过程中不断添加新功能

## 5. 运行与测试方式

- 本地运行方式：
  1. 克隆仓库并进入项目目录
     ```bash
     git clone <仓库地址>
     cd mytodolist
     ```

  2. 创建并激活虚拟环境
     ```bash
     python -m venv venv
     # Windows
     venv\Scripts\activate
     # macOS/Linux
     source venv/bin/activate
     ```

  3. 安装依赖
     ```bash
     pip install -r requirements.txt
     ```

  4. 配置环境变量，创建`.env`文件：
     ```
     SECRET_KEY=your_secret_key
     JWT_SECRET_KEY=your_jwt_secret_key
     SQLALCHEMY_DATABASE_URI=mysql+mysqlconnector://username:password@localhost/db_name
     ```

  5. 初始化数据库
     ```bash
     在个人MySQL服务器中创建mytodolist数据库
     ```

  6. 启动应用
     ```bash
     python backend/run.py
     ```

  7. 访问应用：打开浏览器访问 `http://127.0.0.1:5000`

- 已测试环境：
  - Python 3.x
  - MySQL 5.7+
  - 主流浏览器（Chrome, Firefox, Edge）

- 已知问题与不足：
  - 未实现任务提醒的精确时间设置
  - 缺少批量操作任务的功能
  - 部分前端页面设计不够完善

## 6. 总结与反思

- 改进方向：
  - 添加任务统计和数据分析功能，展示完成率和效率趋势
  - 增加团队任务分享和协作功能
  - 集成邮件项目
  - 任务提醒反馈，可以接受用户回复

- 实现亮点：
  - 完整的用户认证流程，基于JWT的安全验证
  - 灵活的标签管理系统，支持自定义标签和颜色
  - 多维度的任务筛选和管理功能
  - 前后端分离架构，便于独立扩展和维护
  - 完善的数据验证和错误处理机制
  - 实现任务到期提醒，并可以查看任务详细信息