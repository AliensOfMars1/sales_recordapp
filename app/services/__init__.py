from flask import Blueprint
services_bp = Blueprint('services', __name__)
from app.services import routes