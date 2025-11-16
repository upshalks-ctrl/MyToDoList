from datetime import datetime, timedelta, timezone
import threading
import time
from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room
from backend.app.models.models import Todo, User
from backend.app import db, socketio


class ReminderService:
    """
    提醒服务类，用于定期检查即将到期的任务并发送提醒
    """
    def __init__(self, app: Flask):
        self.app = app
        self.is_running = False
        self.thread = None
        self.check_interval = 60  # 检查间隔，单位：秒
    
    def start(self):
        """
        启动提醒服务
        """
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._run)
            self.thread.daemon = True
            self.thread.start()
            print("提醒服务已启动")
    
    def stop(self):
        """
        停止提醒服务
        """
        if self.is_running:
            self.is_running = False
            if self.thread:
                self.thread.join()
            print("提醒服务已停止")
    
    def _run(self):
        """
        服务运行的主循环
        """
        while self.is_running:
            try:
                self._check_upcoming_tasks()
            except Exception as e:
                print(f"提醒服务检查任务时出错: {e}")
            
            # 等待下一次检查
            for _ in range(self.check_interval):
                if not self.is_running:
                    break
                time.sleep(1)
    
    def _check_upcoming_tasks(self):
        """
        检查所有用户的即将到期任务，在截止时间前1小时、15分钟和5分钟发送提醒
        """
        import json
        now = datetime.utcnow()  # 使用UTC时间（naive datetime），与数据库中的时间保持一致
        
        # 定义需要检查的时间点
        reminder_timepoints = [
            ('1h', timedelta(hours=1)),  # 1小时前
            ('15m', timedelta(minutes=15)),  # 15分钟前
            ('5m', timedelta(minutes=5))  # 5分钟前
        ]
        
        # 使用应用上下文查询数据库
        with self.app.app_context():
            # 查询所有未完成且有截止日期的任务
            tasks_with_due_date = Todo.query.filter(
                Todo.completed.is_(False),
                Todo.due_date.isnot(None)
            ).all()
            
            # 按用户分组需要发送的提醒
            user_reminders = {}
            
            for task in tasks_with_due_date:
                # 获取已发送的提醒列表
                reminders_sent = json.loads(task.reminders_sent) if task.reminders_sent else []
                
                for timepoint_name, time_delta in reminder_timepoints:
                    # 计算提醒时间点
                    reminder_time = task.due_date - time_delta
                    
                    # 检查是否到达提醒时间点，且该时间点的提醒尚未发送
                    if now >= reminder_time and now < reminder_time + timedelta(minutes=1) and timepoint_name not in reminders_sent:
                        # 记录已发送的提醒
                        reminders_sent.append(timepoint_name)
                        task.reminders_sent = json.dumps(reminders_sent)
                        
                        # 将任务添加到用户提醒列表
                        if task.user_id not in user_reminders:
                            user_reminders[task.user_id] = []
                        
                        user_reminders[task.user_id].append({
                            'id': task.id,
                            'title': task.title,
                            'description': task.description,
                            'due_date': task.due_date.isoformat() if task.due_date else None,
                            'priority': task.priority,
                            'reminder_time': timepoint_name
                        })
            
            # 保存所有更新
            db.session.commit()
            
            # 向每个有即将到期任务的用户发送提醒
            for user_id, tasks in user_reminders.items():
                self._send_reminder(user_id, tasks)
    
    def _send_reminder(self, user_id: int, tasks: list):
        """
        向指定用户发送提醒
        """
        # 通过WebSocket发送提醒
        # 用户需要在前端连接WebSocket并提供user_id作为房间号
        
        # 统计不同类型的提醒数量
        reminder_counts = {}
        for task in tasks:
            timepoint = task.get('reminder_time')
            reminder_counts[timepoint] = reminder_counts.get(timepoint, 0) + 1
        
        # 构建消息内容
        message_parts = []
        if reminder_counts.get('1h', 0) > 0:
            message_parts.append(f"{reminder_counts['1h']}个任务将在1小时后到期")
        if reminder_counts.get('15m', 0) > 0:
            message_parts.append(f"{reminder_counts['15m']}个任务将在15分钟后到期")
        if reminder_counts.get('5m', 0) > 0:
            message_parts.append(f"{reminder_counts['5m']}个任务将在5分钟后到期")
        
        message = "；".join(message_parts) + "！"
        
        socketio.emit('reminder', {
            'tasks': tasks,
            'message': message
        }, room=str(user_id))

# 创建提醒服务实例
reminder_service = None

# WebSocket事件处理
@socketio.on('connect')
def handle_connect():
    """
    处理客户端连接事件
    """
    print('客户端已连接:', request.sid)

@socketio.on('disconnect')
def handle_disconnect():
    """
    处理客户端断开连接事件
    """
    print('客户端已断开连接:', request.sid)

@socketio.on('join_room')
def handle_join_room(user_id):
    """
    处理用户加入房间事件
    """
    join_room(str(user_id))
    print(f'用户 {user_id} 已加入房间')

def init_reminder_service(app: Flask):
    """
    初始化提醒服务
    """
    global reminder_service
    reminder_service = ReminderService(app)
    
    # 启动提醒服务
    reminder_service.start()
    
    return reminder_service

