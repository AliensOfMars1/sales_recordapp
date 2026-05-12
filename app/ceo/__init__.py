from flask import Blueprint

ceo_bp = Blueprint('ceo', __name__, url_prefix='/ceo')

from app.ceo import routes



