from flask import Blueprint
from flask import session,redirect,request

admin_blueprint = Blueprint("admin", __name__, url_prefix="/admin")

from . import views

@admin_blueprint.before_request
def login_status():
    my_list = ["/admin/login"]
    if request.path not in my_list:
        if "admin_user_id" not in session:
            return redirect("/admin/login")