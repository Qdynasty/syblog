import os
import random
import string

import pathlib

from info import db
from . import profile_blueprint
from info.utils.common import longin_wrappes
from flask import request,render_template,jsonify,g
from info.response_code import RET
from flask import current_app
from info.utils.image_storage import storage
from info.models import News, User, Category
from info import constants

@profile_blueprint.route("/")
@longin_wrappes
def user():
    data={
        "user":g.user.to_login_dict() if g.user else None
    }
    return render_template("news/user.html", data = data)

# 获取性别，昵称，签名， 基本资料更改
@profile_blueprint.route('/user_base_info',methods = ["post", "get"])
@longin_wrappes
def user_base_info():
    if request.method == "GET":
        data = {
            "user":g.user.to_dict() if g.user else None
        }
        return render_template("news/user_base_info.html",data=data)

    signature=request.json.get("signature")
    nick_name=request.json.get("nick_name")
    gender=request.json.get("gender")

    if not all([signature,nick_name,gender]):
        return jsonify(errno=RET.NODATA, errmsg="数据不全")

    user = g.user
    user.nick_name = nick_name
    user.gender = gender
    user.signature = signature

    try:

        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库链接失败")

    return jsonify(errno=RET.OK, errmsg="")

# 上传图片
@profile_blueprint.route('/user_pic_info',methods = ["post", "get"])
@longin_wrappes
def user_pic_info():
    if request.method =="GET":
        data= {
        "user":g.user.to_login_dict
        }
        return render_template("news/user_pic_info.html", data = data)
    avatar = request.files.get("avatar")
    print(avatar,"vvvvvvvv")
    if not avatar:
        return jsonify(errno=RET.NODATA, errmsg="没有数据")

    try:
        file_name = storage(avatar.read())
        print(file_name,"dddddddddddddddddd")
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, ermsg="数据错误")

    user = g.user
    user.avatar_url = file_name
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库链接失败")

    return jsonify(errno=RET.OK, errmsg="",data = user.to_login_dict())

# 我的关注的作者
@profile_blueprint.route("/user_follow",methods = ["post","get"])
@longin_wrappes
def user_follow():
    if request.method =="GET":
        try:
            page = int(request.args.get("page", 1))

            paginate = g.user.authors.order_by(User.id.desc()). \
                paginate(page, constants.USER_FOLLOWED_MAX_COUNT, False)
            data = {
                    "authors_list": [author.to_dict() for author in paginate.items],
                    "page": page,
                    "tole_page":paginate.pages
            }
        except Exception as e:
            data = {
                "authors_list": [],
                "page": 1,
                "tole_page": 0
            }
        return render_template("news/user_follow.html",data=data)
    # action = request.json.get("action")
    # user_id = request.json.get("user_id")
    # if not all ([action, user_id]):
    #     return jsonify(errno=RET.NODATA, errmsg="数据不全")


# 更改密码
@profile_blueprint.route("/user_pass_info",methods = ["post","get"])
@longin_wrappes
def user_pass_info():
    if request.method=="GET":

        return render_template("news/user_pass_info.html")

    old_password = request.json.get("old_password")
    new_password1 = request.json.get("new_password1")
    new_password2 = request.json.get("new_password2")

    if not all([old_password, new_password1, new_password2]):
        return jsonify(errno=RET.NODATA, errmsg="数据不全")
    user = g.user
    try:
        # 调用原来的models中的方法
       if not user.check_password(old_password):
           return jsonify(errno=RET.DATAERR, errmsg = "元密码错误")
    except Exception as e:
        return jsonify(errno = RET.DATAERR, errmsg="数据库链接失败")

    user.password = new_password1

    try:
      db.session.commit()
    except Exception as e:
        return jsonify(errno = RET.DATAERR, errmsg="数据库链接失败")
    return jsonify(errno = RET.OK, errmsg = "")

# 我收藏的新文
@profile_blueprint.route("/user_collection",methods = ["post","get"])
@longin_wrappes
def user_collection():
    try:

        # page = int(request.args.get("pages"))
        page = int(request.args.get('page', 1))
        paginate =  g.user.collection_news.order_by(News.id.desc()).\
            paginate(page,constants.USER_COLLECTION_MAX_NEWS,False)

        data={
            "new_list":[new.to_index_dict() for new in paginate.items],
            "page":page,
            "tole_page":paginate.pages

        }
        print(data)
    except Exception as e:
        data = {
            "new_list":[],
            "page": 1,
            "tole_page":0
            }
    return render_template("news/user_collection.html",data = data)

# 新闻发布
@profile_blueprint.route("/user_news_release",methods=["post", "get"])
@longin_wrappes
def user_news_release():
    if request.method =="GET":

        category_list1 = Category.query.all()
        category_list2=[category.to_dict() for category in category_list1]
        data = {
            "category": category_list2
        }
        return render_template("news/user_news_release.html", data=data)

    # post 上传 新闻文章给
    title=request.form.get("title")
    disget = request.form.get("digest")
    content = request.form.get("content")
    avatar = request.files.get("avatar")
    category_id = request.form.get("category_id")

    if not all ([title, disget, content, avatar]):
        return jsonify(errno=RET.NODATA, errmsg="数据不全")

    # todo 图片处理
    # 生成随机字符串，防止图片名字重复
    ran_str = ''.join(random.sample(string.ascii_letters + string.digits, 16))
    # # 获取图片文件 name = upload
    # img = request.files.get('upload')
    # 定义一个图片存放的位置 存放在static下面
    # base_path = pathlib.Path(__file__).parent.parent
    # print(base_path)
    # path = os.path.join(base_path,"static/news/news_images/")
    path = "info/static/news/news_images/"
    # 图片名称 给图片重命名 为了图片名称的唯一性
    imgName = ran_str + avatar.filename
    # 图片path和名称组成图片的保存路径
    file_path = path + imgName
    # 保存图片
    avatar.save(file_path)
    # 这个是图片的访问路径，需返回前端（可有可无）


    try:
        category = Category.query.get(category_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库链接失败")
    if not category:
        return jsonify(errno=RET.NODATA, errmsg="数据不正确")

    # try:
    #     file_name = storage(avatar.read())
    # except Exception as e:
    #     return jsonify(errno=RET.NODATA, errmsg="图片上传失败")

    news = News()
    news.title = title
    news.digest = disget
    news.content=content
    news.index_image_url = imgName
    news.category_id=int(category_id)
    news.source = g.user.nick_name
    news.user_id=g.user.id
    db.session.add(news)
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库链接失败")
    return jsonify(errno=RET.OK, errmsg="")

# 我发布的新闻的列表
@profile_blueprint.route("/user_news_list")
@longin_wrappes
def user_news_list():
    try:
        page=int(request.args.get("page", 1))
    except Exception as e:
        page=1

    try:
        paginate = g.user.news_list.order_by(News.id.desc()).paginate(page,6,False)

        data = {
            "news_list":[paginate.to_list_dict() for paginate in paginate.items],
            "tole_page":paginate.pages,
            "page":page
        }
    except Exception as e:

        data = {
            "news_list": [],
            "tole_page": 0,
            "page": 1
        }
    return render_template("news/user_news_list.html", data=data)