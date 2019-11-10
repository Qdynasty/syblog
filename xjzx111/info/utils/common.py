from info.models import News,User
from info import constants
from flask import session,g
import functools
def get_click_list():
    click_list1 = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    click_list2 = [click.to_click_dict() for click in click_list1]
    return click_list2

def longin_wrappes(view):
    @functools.wraps(view)
    def fun(*args, **kwargs):
        if "user_id" in session:

            g.user = User.query.get(session.get("user_id"))
            print("g.user:",g.user)
        else:
            g.user =None

        return view(*args,**kwargs)
    return fun