# @author wangchao

from flask import current_app
from flask_migrate import Migrate,MigrateCommand
from flask_script import Manager
from info import create_app, db
from info.models import User

# 调用create_app 传入工厂模式
app = create_app("development")
# 通过manager管理app
manager = Manager(app)
# 数据迁移
Migrate(app,db)
manager.add_command("db",MigrateCommand)

@manager.option("-n",dest="name")
@manager.option("-p",dest="password")
def createsuperuser(name, password):
    try:
        user = User.query.filter_by(mobile=name).count()
        # User.query.filter_by(mobile=name) 返回是一个新的查询
        print(user)
        if user:
            print("用户已经存在")
            return
    except Exception as e:
        current_app.logger.error(e)
        print("数据库链接失败")
        return
    user = User()
    user.mobile=name
    user.nick_name=name
    user.password=password
    user.is_admin = True
    db.session.add(user)
    try:
        db.session.commit()
    except Exception as e:
        print("数据库链接失败")
        return
    print("创建管理员成功")

if __name__ == '__main__':
    manager.run()