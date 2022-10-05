from flask import Blueprint, url_for
from werkzeug.utils import redirect

from app.models import Question

bp = Blueprint('main', __name__, url_prefix='/')


@bp.route('/hello')
def hello_hamonica():
    return 'Hello, Hamonica!'


@bp.route('/')
def index():
    return redirect(url_for('question._list'))
