from . import new_blueprint
from flask import render_template,session,g,request, jsonify,current_app
from info.models import News,Comment,CommentLike, User
from info import constants, db
from info.utils.common import longin_wrappes
from info.response_code import RET


@new_blueprint.route("/<int:new_id>")
@longin_wrappes
def new(new_id):
    # 获取当新闻对象
    new = News.query.get_or_404(new_id)
    # 访问量加1
    new.clicks+=1
    db.session.commit()
    # 判断是否收藏新闻
    if g.user and new in g.user.collection_news:
        is_collect = True
    else:
        is_collect = False

    if g.user is None:
        user1 = g.user
    else:
        user1 = g.user.to_login_dict()
    # 找到新闻的所有不含有parent的所有新闻
    comment_list1 = new.comments.filter(Comment.parent_id==None).order_by(Comment.id.desc())
    comment_list12 = [comment.to_dict() for comment in comment_list1]
    if g.user:
        # 获取当前新闻所有评论的编号
        comment_id = [comment.id for comment in comment_list1]
        # 查询点赞表:当前新闻的评论、当前用户点赞过的数据
        likes = CommentLike.query.filter_by(user_id=g.user.id).\
            filter(CommentLike.comment_id.in_(comment_id))
        likes_list = [like.comment_id for like in likes]
        for comment in comment_list12:
            comment["is_like"] = comment.get("id") in likes_list


# 点击排行
    from info.utils.common import get_click_list
    click_list2 = get_click_list()



    data={
        "news":new,
        'news_list':click_list2,
        "user":user1,
        "is_collect":is_collect,
        "comment":comment_list12

    }
    print(data)

    return render_template("news/detail.html",data = data)
# 新闻收藏 向数据库中加数据
@new_blueprint.route("/news_collect",methods = ["post"])
@longin_wrappes
def new_collect(): # 新闻收藏
    news_id = request.json.get("news_id")
    action = request.json.get("action")  # 获得是否是收藏
    print(news_id)
    if not all([news_id,action]):
        return jsonify(errno = RET.NODATA,errmsg = "数据不全")
    if g.user is None:
        return jsonify(errno = RET.NODATA,errmsg = "用户没有登录")
    try:
        news = News.query.get(news_id) # 获取当前新闻对象
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="数据库连接失败")
    if news is None:
        return jsonify(errno=RET.NODATA,errmsg="数据无效")
    if action not in ["cancel_collect","collect"]:  # 判断
        return jsonify(errno=RET.DATAERR,errmsg= "数据不正确")
    user = g.user
    if action == "collect":
        # 通过中间表收藏新闻
        user.collection_news.append(news)
    else:
        user.collection_news.remove(news)
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据提交失败")
    return jsonify(errno=RET.OK, errmsg="jjjj")

# 新闻评论向数据库中加数据
@new_blueprint.route("/news_comment",methods = ["post"])
@longin_wrappes
def news_comment():
    # 新闻评论
    news_id = request.json.get("news_id")
    # 获得新闻的内容
    msg = request.json.get("comment")
    # 父子评论的id comment.id
    parent_id = request.json.get("parent_id")

    if not all ([news_id, msg]):
        return jsonify(errno=RET.NODATA, errmsg="数据不全")
    if g.user is None:
        return jsonify(errno=RET.NODATA, errmsg="用户没有登录")
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库连接失败')
    if news is None:
        return jsonify(errno=RET.NODATA, errmsg="数据无效")
    comment_new = Comment()
    if parent_id:
        # 向评论表中加id 自关联id 代表是子评论
        comment_new.parent_id = parent_id
    comment_new.user_id = g.user.id
    comment_new.news_id = int(news_id)
    comment_new.content = msg
    try:
        db.session.add(comment_new)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库链接失败")

    if parent_id:
        data = comment_new.to_back_dict()
    else:
        data = comment_new.to_dict()
    return jsonify(errno=RET.OK, errmsg="", data=data)

# 点赞向据库中家属据
@new_blueprint.route('/comment_like',methods = ["post"])
@longin_wrappes
def comment_like():
    # 点赞
    comment_id=request.json.get("comment_id")
    action = request.json.get("action") # 有无点赞过
    news_id = request.json.get("news_id")
    print(action)
    if not all([comment_id,news_id]):
        return jsonify(errno=RET.NODATA, errmsg="数据不全")
    if g.user is None:
        return jsonify(errno=RET.NODATA, errmsg="用户没有登录")
    # 用户id
    user = g.user.id
    # 获得父级评论的对象
    comment = Comment.query.get(comment_id)
    hh=comment.like_count
    print(hh,"hhhhhhhh")
    if action == "add":
        # 点赞表的对象
        like = CommentLike()
        # 获得的数值是二进制的
        like.comment_id = int(comment_id)
        like.user_id = user

        try:
            comment.like_count+=1
            db.session.add(like)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="数据库链接失败1")
    else:
        # 从点赞表中找到当前用户和当前评论的这个
        like=CommentLike.query.filter_by(comment_id=comment_id,user_id=user).first()

        try:
            comment.like_count-=1
            db.session.delete(like)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="数据库链接失败2")
    return jsonify(errno=RET.OK, errmsg="",data = hh)

# 关注作者向数据库存数据
@new_blueprint.route("/followed_user",methods=["post"] )
@longin_wrappes
def followed_user():
    action = request.json.get("action")
    user_id = request.json.get("user_id")
    print(action)
    if not all ([action, user_id]):
        return jsonify(errno=RET.NODATA,errmsg="数据不全")

    if not g.user:
        return jsonify(errno=RET.NODATA, errmsg="用户没有登录")
    if action not in ["follow","unfollow"]:
         return jsonify(errno=RET.NODATA, errmsg="数据不正确")
    try:

        author = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库连接有无")

    if action == "follow":
        if author not in g.user.authors:
            g.user.authors.append(author)
            try:
                db.session.commit()
            except Exception as e:
                current_app.logger.error(e)
                return jsonify(errno=RET.DBERR, errmsg="数据库连接错误1")
    else:
        g.user.authors.remove(author)
        try:
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="数据库连接错误2")

    return jsonify(errno=RET.OK, errmsg="")


