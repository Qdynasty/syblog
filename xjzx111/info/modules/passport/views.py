# 用户登陆突出功能
from . import passport_blueprint
from libs.captcha.captcha import captcha
from flask import request,make_response,render_template,session
from info import redis_store, db
from info import constants
from flask import jsonify
from info.response_code import RET
from info.models import User
import re,random
from info.utils.sms import sendTemplateSMS
from datetime import datetime
# 产生随机验证码
@passport_blueprint.route("/image_code")
def image_code():
    # 第三方生成随机验证码图片
    text, code, image = captcha.generate_captcha()
    code_id = request.args.get("code_id")

    # 图片保存到redis中
    redis_store.setex(code_id,constants.IMAGE_CODE_REDIS_EXPIRES,code)

    response = make_response(image)

    response.headers["Content-Type"] = "image/png"

    return response
# 注册前信息的验证
@passport_blueprint.route("/sms_code",methods = ["post"])
def sms_code():
    mobile = request.json.get("mobile")
    image_request = request.json.get("image_code")
    image_code_id = request.json.get("image_code_id")
    print(image_request)
    image_redis = redis_store.get(image_code_id)
    print(image_redis.decode())
    if image_redis is None:
        return jsonify(errno=RET.NODATA, errmsg='图形验证码过期')

    if image_request != image_redis.decode():
        return jsonify(errno=RET.DATAERR, errmsg="图片验证错误")

    if not re.match(r"^1[35678]\d{9}$",mobile):
        return jsonify(errno=RET.NODATA, errmsg='手机号格式错误')

    mobile_count = User.query.filter_by(mobile = mobile).count()
    if mobile_count>0:
        return jsonify(errno=RET.DATAEXIST, errmsg='手机号已经被使用')

    smscode = str(random.randint(100000,999999))
    print(smscode)
    # 云平台发送手机密码
    sendTemplateSMS(mobile,[smscode,5],1)
    print(smscode)
    # 把验证码存在redis中 用手机好作为id
    redis_store.setex(mobile,constants.SMS_CODE_REDIS_EXPIRES,smscode)

    return jsonify(errno = RET.OK, errmsg = "")

# 注册信息提交
@passport_blueprint.route("/register",methods = ["post"])
def register():
    mobile = request.json.get("mobile")
    password = request.json.get("password")
    smscode = request.json.get("smscode")
    print(smscode,"ddddddddddddddd")
    if not all([mobile,password,smscode]):
        return jsonify(erron = RET.NODATA,errmsg = "信息不全")

    # 获得手机验证码
    smscode_redis = redis_store.get(mobile)
    print(smscode_redis.decode())

    if smscode_redis is None:
        return jsonify(erron = RET.NODATA,errmsg = "没有手机验证吗过期")

    if smscode != smscode_redis.decode():

        return jsonify(erron = RET.DATAERR, errmsg = "手机验证码部正确")

    user = User()
    user.mobile = mobile

    user.nick_name = mobile
    user.password = password
    db.session.add(user)
    db.session.commit()


    return jsonify(erron = RET.OK, errmsg = "")

# 登陆信息验证
@passport_blueprint.route('/login', methods=['POST'])
def login():

    mobile = request.json.get('mobile')
    password = request.json.get('password')
    if not all([mobile, password]):
        return jsonify(errno=RET.NODATA, errmsg='参数不完整')

    user = User.query.filter_by(mobile=mobile).first()

    if user is None:
        return jsonify(errno=RET.DATAERR, errmsg='手机号错误')

    if user.check_password(password):

        session['user_id'] = user.id
        session['nick_name'] = user.nick_name
        now = datetime.now()
        day_now = datetime(now.year, now.month, now.day, now.hour,now.minute)
        user.update_time = day_now
        db.session.commit()
        return jsonify(errno=RET.OK, errmsg='')
    else:
        return jsonify(errno=RET.DATAERR, errmsg='密码错误')

@passport_blueprint.route("/logout", methods = ["post"])
def logout():
    session.pop("user_id")
    session.pop("nick_name")
    return jsonify(erron =RET.OK, errmasg="")

