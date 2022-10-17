from datetime import datetime
from flask import Blueprint, render_template, request, url_for, g, flash
from werkzeug.utils import redirect

from .. import db
from app.models import Question, Answer, User
from app.forms import QuestionForm, AnswerForm, ExtraSearchForm
from app.views.auth_views import login_required
from sqlalchemy import and_, or_, not_

bp = Blueprint('question', __name__, url_prefix='/question')


@bp.route('/list/', methods=('GET', 'POST'))
def _list():
    page = request.args.get('page', type=int, default=1)
    kw = request.args.get('kw', type=str, default='')
    
    question_list = Question.query.order_by(Question.create_date.desc())
    form = ExtraSearchForm()
    kw2 = request.args.get('kw2', type=str, default='')
    operator = request.args.get('operator')
    # operator = form.operator.data

    # 키워드 한개 검색
    if kw and kw2 == '':
        search = '%%{}%%'.format(kw)
        sub_query = db.session.query(Answer.question_id, Answer.content, User.username) \
            .join(User, Answer.user_id == User.id).subquery()
        question_list = question_list \
            .join(User).outerjoin(sub_query, sub_query.c.question_id == Question.id).filter(
                Question.subject.ilike(search) |  # 질문제목
                Question.content.ilike(search) |  # 질문내용
                User.username.ilike(search) |  # 질문작성자
                sub_query.c.content.ilike(search) |  # 답변내용
                sub_query.c.username.ilike(search)  # 답변작성자
                ) \
            .distinct()
        question_list = question_list.paginate(page, per_page=20)
        return render_template('question/question_list.html', question_list=question_list, page=page, kw=kw, form=form)
            
    #And, Or, Not 연산하기
    # if request.method == 'POST':
        # kw2 = request.form.get('kw2', type=str, default='')
    if kw2:
        if operator == "AND":
            search1 = '%%{}%%'.format(kw)
            search2 = '%%{}%%'.format(kw2)
            sub_query = db.session.query(Answer.question_id, Answer.content, User.username) \
                .join(User, Answer.user_id == User.id).subquery()
            question_list = question_list \
                .join(User).outerjoin(sub_query, sub_query.c.question_id == Question.id).filter(
                    and_(Question.subject.ilike(search1), Question.subject.ilike(search2)) |  # 질문제목
                    and_(Question.content.ilike(search1), Question.content.ilike(search2)) |  # 질문내용
                    and_(User.username.ilike(search1), User.username.ilike(search2)) |  # 질문작성자
                    and_(sub_query.c.content.ilike(search1), sub_query.c.content.ilike(search2)) |  # 답변내용
                    and_(sub_query.c.username.ilike(search1), sub_query.c.username.ilike(search2))  # 답변작성자
                ) \
            .distinct()

        elif operator == "OR":
            search1 = '%%{}%%'.format(kw)
            search2 = '%%{}%%'.format(kw2)
            sub_query = db.session.query(Answer.question_id, Answer.content, User.username) \
                .join(User, Answer.user_id == User.id).subquery()
            question_list = question_list \
                .join(User).outerjoin(sub_query, sub_query.c.question_id == Question.id).filter(
                    or_(Question.subject.ilike(search1), Question.subject.ilike(search2)) |  # 질문제목
                    or_(Question.content.ilike(search1), Question.content.ilike(search2)) |  # 질문내용
                    or_(User.username.ilike(search1), User.username.ilike(search2)) |  # 질문작성자
                    or_(sub_query.c.content.ilike(search1), sub_query.c.content.ilike(search2)) |  # 답변내용
                    or_(sub_query.c.username.ilike(search1), sub_query.c.username.ilike(search2))  # 답변작성자
                ) \
            .distinct()
        
        elif operator == "NOT":
            search1 = '%%{}%%'.format(kw)
            # search2 = '%%{}%%'.format(kw2)
            search2 = str(kw2)
            sub_query = db.session.query(Answer.question_id, Answer.content, User.username) \
                .join(User, Answer.user_id == User.id).subquery()
            question_list = question_list \
                .join(User).outerjoin(sub_query, sub_query.c.question_id == Question.id).filter(
                    Question.subject.ilike(search1) |  # 질문제목
                    Question.content.ilike(search1) |  # 질문내용
                    User.username.ilike(search1) |  # 질문작성자
                    sub_query.c.content.ilike(search1) |  # 답변내용
                    sub_query.c.username.ilike(search1)  # 답변작성자
                ).filter(
                    ~Question.subject.contains(search2),    # 질문제목
                    ~Question.content.contains(search2), # 질문내용
                    # ~User.username.contains(search2),  # 질문작성자
                    # ~sub_query.c.content.contains(search2), # 답변내용
                    # ~sub_query.c.username.contains(search2)  # 답변작성자
                ) \
            .distinct()

    question_list = question_list.paginate(page, per_page=20)
    return render_template('question/question_list.html', question_list=question_list, page=page, kw=kw, operator=operator, kw2=kw2, form=form)


@bp.route('/detail/<int:question_id>/')
def detail(question_id):
    form = AnswerForm()
    question = Question.query.get_or_404(question_id)
    return render_template('question/question_detail.html', question=question, form=form)


@bp.route('/create/', methods=('GET', 'POST'))
@login_required
def create():
    form = QuestionForm()
    if request.method == 'POST' and form.validate_on_submit():
        question = Question(subject=form.subject.data, content=form.content.data,
                            create_date=datetime.now(), user=g.user)
        db.session.add(question)
        db.session.commit()
        return redirect(url_for('main.index'))
    return render_template('question/question_form.html', form=form)


@bp.route('/modify/<int:question_id>', methods=('GET', 'POST'))
@login_required
def modify(question_id):
    question = Question.query.get_or_404(question_id)
    if g.user != question.user:
        flash('수정권한이 없습니다')
        return redirect(url_for('question.detail', question_id=question_id))
    if request.method == 'POST':  # POST 요청
        form = QuestionForm()
        if form.validate_on_submit():
            form.populate_obj(question)
            question.modify_date = datetime.now()  # 수정일시 저장
            db.session.commit()
            return redirect(url_for('question.detail', question_id=question_id))
    else:  # GET 요청
        form = QuestionForm(obj=question)
    return render_template('question/question_form.html', form=form)


@bp.route('/delete/<int:question_id>')
@login_required
def delete(question_id):
    question = Question.query.get_or_404(question_id)
    if g.user != question.user:
        flash('삭제권한이 없습니다')
        return redirect(url_for('question.detail', question_id=question_id))
    db.session.delete(question)
    db.session.commit()
    return redirect(url_for('question._list'))


@bp.route('/vote/<int:question_id>/')
@login_required
def vote(question_id):
    _question = Question.query.get_or_404(question_id)
    if g.user == _question.user:
        flash('본인이 작성한 글은 추천할수 없습니다')
    else:
        _question.voter.append(g.user)
        db.session.commit()
    return redirect(url_for('question.detail', question_id=question_id))