from flask import Blueprint
barbers_bp = Blueprint('barbers', __name__)
from app.barbers import routes