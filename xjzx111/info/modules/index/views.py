from flask import render_template
from flask import request,g
from flask import session,jsonify
from info.utils.common import longin_wrappes
from info import constants
from . import index_blueprint
from info.response_code import RET
from info.models import User,Category,News


@index_blueprint.route("/")
@longin_wrappes
# 主页面显示
def index():
    # user_id = session.get("user_id")
    # if user_id is None:
    #     user = None
    # else:
    #     # 获得登录信息
    #     user = User.query.get(user_id).to_login_dict()
        # 获得新闻分类标题栏
    if g.user==None:
        user1 = g.user
    else:
        user1 = g.user.to_login_dict()

    category_list1 = Category.query.all()
    category_list2 = [category.to_dict() for category in category_list1]
    # 获得点击排行新闻
    # new_list1 = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    # new_list2 = [new.to_click_dict() for new in new_list1]

    from info.utils.common import get_click_list
    new_list2 = get_click_list()

    data = {
        "user":user1,
        "category_list":category_list2,
        "news_list":new_list2
        }
    return render_template("news/index.html", data=data)

# 主页面新闻列表显示
@index_blueprint.route("/newslist")
def newslist():
    #
    page = request.args.get("page") # 页数
    cid = request.args.get("cid") # 分类id
    per_page = request.args.get("per_page") # 每页多少条数据，如果不传，默认10条
    if not all([page, cid, per_page]):
        return jsonify(errno = RET.NODATA, errmsg = "数据不全")
    pagination =News.query
    if int(cid)!= 0:
        pagination = pagination.filter_by(category_id=cid)

    pagination = pagination.order_by(News.id.desc()).\
        paginate(int(page),int(per_page), False)
    newslist1 = pagination.items # 获取当前页的数据
    toles_pages = pagination.pages # 获取总页数

    new_dict_list = [new.to_index_dict() for new in newslist1]

    data = {
        "erron":RET.OK,
        "errmsg":"",
        "cid":cid,
        "newsList":new_dict_list,
        "current_page":page,
        "totalPage":toles_pages


    }
    return jsonify(data)





