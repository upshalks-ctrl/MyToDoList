from backend.app import create_app, db, socketio

app = create_app()

# 创建数据库表
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    socketio.run(app, debug=True)