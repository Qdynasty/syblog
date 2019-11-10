from flask import redirect
from flask import session, current_app
from info import constants, db
from . import admin_blueprint
from flask import render_template,request
from info.models import User,News, Category
from flask import current_app,jsonify
from datetime import datetime, timedelta
from info.response_code import RET
from info.utils.image_storage import storage

@admin_blueprint.route("/login", methods = ["post", "get"])
def login():
    if request.method=="GET":
        data={"msg":""}
        return render_template("admin/login.html", data=data)

    username = request.form.get("username")
    password = request.form.get("password")

    if not all([username, password]):
        data={"msg":"数据不全"}
        return render_template("admin/login.html", data=data)

    try:
        user=User.query.filter_by(mobile=username, is_admin=True).first()

    except Exception as e:
        current_app.logger.error(e)
        data={"msg":"数据库链接失败"}
        return render_template("admin/login.html", data = data)
    if not user:
        data={"msg":"用户不存在"}
        return render_template("admin/login.html", data=data)

    if user.check_password(password):
        session["admin_user_id"] = user.id
        return redirect('/admin/')
    else:
        data={"msg":"密码错误"}
        return render_template("admin/login.html", data=data)

@admin_blueprint.route("/logout")
def logout():
    session.pop("admin_user_id")
    return redirect("/admin/login")

@admin_blueprint.route("/")
def index():
    try:
        user=User.query.get(session.get("admin_user_id"))
    except Exception as e:
        current_app.logger.error(e)
        print("")

    data = {
        "name":user.nick_name if user else None,
        "avatar":constants.QINIU_DOMIN_PREFIX+user.avatar_url
    }

    return render_template("admin/index.html", data=data)


@admin_blueprint.route("/user_count")
def user_count():

    user_totle = User.query.filter_by(is_admin=False).count()

    now = datetime.now()
    print(User.query.all())
    month_now = datetime(now.year, now.month,1)
    month_user = User.query.filter\
        (User.create_time>=month_now, User.is_admin==False).count()

    day_now = datetime(now.year,now.month, now.day)

    day_user = User.query.filter\
        (User.create_time>=day_now, User.is_admin==False).count()

    xtime = []
    ycount = []
    for i in range(10):
        begin_time = day_now - timedelta(days=i+1)
        end_time = day_now  - timedelta(days=i)
        xtime.append(begin_time.strftime("%Y-%m-%d"))
        # count = User.query.filter\
        #     (User.update_time>=begin_time,
        #      User.update_time<=end_time,User.is_admin==False).count()


        count = User.query.filter_by(is_admin=False). \
            filter(User.update_time >= begin_time, User.update_time <= end_time).count()

        ycount.append(count)
    xtime.reverse()
    ycount.reverse()
    print(xtime)
    print(ycount)
    data={
        "user_count":user_totle,
        "month_user":month_user,
        "day_user":day_user,
        "xtime":xtime,
        "ycount":ycount
    }

    return render_template("admin/user_count.html", data=data)


@admin_blueprint.route("/user_list")
def user_list():
    try:
        page = int(request.args.get("page",1))

    except Exception as e:
        page = 1

    try:
        user = User.query.all()

        paginate = User.query.filter(User.is_admin==False).paginate(page,2,False)



        data ={
            "user":[user.to_login_dict() for user in paginate.items],
            "tole_page":paginate.pages,
            "page":page
        }
        print(data)
    except Exception as e:
        data = {
            "user": [],
            "tole_page":0,
            "page": 1
        }
    return render_template("admin/user_list.html", data=data)


@admin_blueprint.route("/news_review")
# 评论：review
def news_review():
    title = request.args.get("title","")
    page = int(request.args.get("page",1))

    try:
        pagination = News.query.filter_by(status=1)
        if title:
            pagination = pagination.filter(News.title.contains(title))

        paginate = pagination.order_by(News.id.desc()).paginate(page, 3, False)
        data = {
            "news": [new.to_list_dict() for new in paginate.items],
            "tole_pages": paginate.pages,
            "pages": page,
            'title': title
        }
    except Exception as e:
        data = {
            "news": [],
            "tple_pages": 0,
            "pages": 1
        }


    return render_template("admin/news_review.html",data = data)


@admin_blueprint.route("/news_review_detail",methods = ["post","get"])
def news_review_detail():# detail 详细数据
    if request.method =="GET":
        new_id = request.args.get("news_id")
        # try:
        news = News.query.get(new_id)
        print(new_id,"sssssssssssssssss")
        # except Exception as e:
        #     current_app.logger.error(e)
        data={
            "news":news
        }
        return render_template("admin/news_review_detail.html", data=data)
    news_id = request.json.get("news_id")
    action = request.json.get("action")
    reason = request.json.get("reason")
    print(action,"ddddddddddddddd")
    if not all([news_id, action]):
        return  jsonify(errno=RET.NODATA, errmsg = "数据不全")
    try:
        new = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.NODATA, errmsg = "数据错误")
    if not new:
        return jsonify(errno=RET.NODATA, errmsg="数据不正确")
    if action =="accept":
        new.status = 0
    else:
        new.status = -1

        new.resson = reason
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库链接失败")

    return jsonify(errno=RET.OK, errmsg = "")




@admin_blueprint.route("/news_edit")
def news_edit():
    page = int(request.args.get("page", 1))
    title = request.args.get("title","")
    pagination = News.query.filter_by(status=0)
    try:
        if title:
            pagination = pagination.filter(News.title.contains(title))
        paginte = pagination.order_by(News.id.desc()).paginate(page, 5, False)

        data = {
            "news": [i.to_list_dict() for i in paginte.items],
            "tole_page":paginte.pages,
            "page":page,
            "title":title
        }
    except Exception as e:
        data = {
            "news": [],
            "tole_page": 0,
            "page": 1
        }
    return render_template("admin/news_edit.html", data = data)



@admin_blueprint.route("/news_edit_detail", methods = ["post","get"])
def new_edit_detail():
    if request.method=="GET":
        news_id = request.args.get("news_id")
        # global news
        # news = news_id

        print("ssnngggg",news_id)
        try:
            global news
            news = News.query.get(news_id)

            category = Category.query.all()
            data = {
                "news":news,
                "category_name":[i.name for i in category]

            }
        except Exception as e:
            current_app.logger.error(e)
            return redirect("admin/new_edit_detail")

        return render_template("admin/news_edit_detail.html", data = data)
    print(news,"fffffff")
    # new = News.query.get(news)
    new = news
    print(new,"ssss")
    title = request.form.get("title")
    print(title,"ttttttttt")
    print(new.title,"dddddddd")
    # category_add = request.form.get("category")
    digest = request.form.get("digest")
    url = request.files.get("url")
    content = request.form.get("content")

    if content != new.content:
        new.content = content

    if title != new.title:
        new.title = title

    # if category_add != new.category.name:
    #     new.category_id = new.category.id

    if digest != new.digest:
        new.digest = digest

    if url:
        file_name = storage(url.read())
        if new.index_image_url != file_name:
            new.index_image_url = file_name
    try:
        db.session.add(new)
        db.session.commit()
    except Exception as e:
        return jsonify(errno=RET.DBERR, errmsg="数据库链接失败")



    return jsonify(errno = RET.OK, errmsg="")

# 增加更改分类
@admin_blueprint.route("/news_type",methods = ["post","get"])
def news_type():
    if request.method =="GET":
        category = Category.query.all()

        data = {
            "category":category
        }

        return render_template("admin/news_type.html", data=data)
    print("kkkkkkkkkkkk")
    cid = request.json.get("id")
    name = request.json.get("name")

    if not name:
        return jsonify(errno=RET.NODATA, errmsg ="数据不全")
    if cid:
        category_id = Category.query.get(cid)
        category_id.name = name
        try:
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno = RET.DBERR, errmsg = "数据库链接失败")
    else:
        add_category = Category()
        add_category.name = name
        db.session.add(add_category)
        try:
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno = RET.DBERR, errmsg = "数据库链接失败")
    return jsonify(errno=RET.OK, errmsg='')