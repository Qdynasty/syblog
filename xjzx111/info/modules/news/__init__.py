
from flask import Blueprint

new_blueprint = Blueprint("nwe",__name__, url_prefix="/news")

from . import views