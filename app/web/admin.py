import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user
from functools import wraps
from app.config import Config
from app.models.database import get_session, User, Message, Expense
logger = logging.getLogger(__name__)
app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = Config.SECRET_KEY
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
class AdminUser(UserMixin):
    def __init__(self, username):
        self.id = username
@login_manager.user_loader
def load_user(user_id):
    if user_id == Config.ADMIN_USERNAME:
        return AdminUser(user_id)
    return None
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == Config.ADMIN_USERNAME and request.form['password'] == Config.ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        return render_template('login.html', error='用户名或密码错误')
    return render_template('login.html')
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))
@app.route('/')
@admin_required
def dashboard():
    sess = get_session()
    try:
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        total_users = sess.query(User).count()
        total_messages = sess.query(Message).count()
        deleted_messages = sess.query(Message).filter_by(is_deleted=True).count()
        edited_messages = sess.query(Message).filter_by(is_edited=True).count()
        today_messages = sess.query(Message).filter(Message.created_at >= today).count()
        month_start = today.replace(day=1)
        month_expenses = sess.query(Expense).filter(Expense.expense_date >= month_start).all()
        total_income = sum(e.amount for e in month_expenses if e.amount > 0)
        total_expense = sum(abs(e.amount) for e in month_expenses if e.amount < 0)
        balance = total_income - total_expense
        daily = []
        max_count = 1
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            next_day = day + timedelta(days=1)
            count = sess.query(Message).filter(Message.created_at >= day, Message.created_at < next_day).count()
            daily.append({'date': day.strftime('%m-%d'), 'count': count})
            if count > max_count: max_count = count
        return render_template('dashboard.html',
            total_users=total_users, total_messages=total_messages,
            deleted_messages=deleted_messages, edited_messages=edited_messages,
            today_messages=today_messages,
            total_income=total_income, total_expense=total_expense, balance=balance,
            daily=daily, max_daily=max_count, now=datetime.utcnow().strftime('%Y-%m-%d %H:%M'))
    finally:
        sess.close()
@app.route('/messages')
@admin_required
def messages():
    sess = get_session()
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 50
        offset = (page - 1) * per_page
        user_id = request.args.get('user_id', type=int)
        sender_type = request.args.get('sender_type', '')
        show_deleted = request.args.get('show_deleted', 'false') == 'true'
        query = sess.query(Message)
        if user_id:
            query = query.filter_by(user_id=user_id)
        if sender_type:
            query = query.filter_by(sender_type=sender_type)
        if not show_deleted:
            query = query.filter_by(is_deleted=False)
        total = query.count()
        msgs = query.order_by(Message.created_at.desc()).offset(offset).limit(per_page).all()
        users = sess.query(User).all()
        filters_query = f"user_id={user_id}&sender_type={sender_type}&show_deleted={show_deleted}" if any([user_id, sender_type, show_deleted]) else ''
        return render_template('messages.html',
            messages=msgs, users=users, total=total, page=page, per_page=per_page,
            total_pages=(total + per_page - 1)//per_page if total>0 else 1,
            filters={'user_id': user_id, 'sender_type': sender_type, 'show_deleted': show_deleted},
            filters_query=filters_query)
    finally:
        sess.close()
@app.route('/api/messages/<int:message_id>')
@admin_required
def get_message_detail(message_id):
    sess = get_session()
    try:
        msg = sess.query(Message).filter_by(id=message_id).first()
        if not msg:
            return jsonify({'error': '不存在'}), 404
        return jsonify({
            'id': msg.id, 'message_id': msg.message_id, 'content': msg.content,
            'original_content': msg.original_content, 'sender_type': msg.sender_type,
            'content_type': msg.content_type, 'is_edited': msg.is_edited,
            'is_deleted': msg.is_deleted,
            'created_at': msg.created_at.isoformat(),
            'deleted_at': msg.deleted_at.isoformat() if msg.deleted_at else None,
            'user': {'telegram_id': msg.user.telegram_id, 'username': msg.user.username,
                     'first_name': msg.user.first_name} if msg.user else None
        })
    finally:
        sess.close()
@app.route('/api/messages/<int:message_id>/restore', methods=['POST'])
@admin_required
def restore_message(message_id):
    sess = get_session()
    try:
        msg = sess.query(Message).filter_by(id=message_id).first()
        if not msg:
            return jsonify({'error': '不存在'}), 404
        if not msg.is_deleted:
            return jsonify({'error': '未删除'}), 400
        msg.is_deleted = False
        msg.deleted_at = None
        sess.commit()
        return jsonify({'success': True})
    except Exception as e:
        sess.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        sess.close()
@app.route('/expenses')
@admin_required
def expenses():
    sess = get_session()
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 50
        offset = (page - 1) * per_page
        user_id = request.args.get('user_id', type=int)
        category = request.args.get('category', '')
        query = sess.query(Expense)
        if user_id:
            query = query.filter_by(user_id=user_id)
        if category:
            query = query.filter_by(category=category)
        total = query.count()
        exp_list = query.order_by(Expense.expense_date.desc()).offset(offset).limit(per_page).all()
        all_exp = sess.query(Expense).all()
        total_income = sum(e.amount for e in all_exp if e.amount > 0)
        total_expense = sum(abs(e.amount) for e in all_exp if e.amount < 0)
        categories = [c[0] for c in sess.query(Expense.category).distinct().all() if c[0]]
        users = sess.query(User).all()
        return render_template('expenses.html',
            expenses=exp_list, users=users, categories=categories, total=total,
            total_income=total_income, total_expense=total_expense, balance=total_income - total_expense,
            page=page, per_page=per_page, total_pages=(total + per_page - 1)//per_page if total>0 else 1)
    finally:
        sess.close()
@app.route('/users')
@admin_required
def users():
    sess = get_session()
    try:
        users_list = sess.query(User).order_by(User.created_at.desc()).all()
        stats = {}
        for u in users_list:
            msg_count = sess.query(Message).filter_by(user_id=u.id).count()
            exp_count = sess.query(Expense).filter_by(user_id=u.id).count()
            stats[u.id] = {'messages': msg_count, 'expenses': exp_count}
        return render_template('users.html', users=users_list, stats=stats)
    finally:
        sess.close()
@app.route('/api/stats')
@admin_required
def get_stats():
    sess = get_session()
    try:
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        hourly = []
        for h in range(24):
            start = today.replace(hour=h)
            end = today.replace(hour=h+1) if h < 23 else today + timedelta(days=1)
            count = sess.query(Message).filter(Message.created_at >= start, Message.created_at < end).count()
            hourly.append({'hour': h, 'count': count})
        daily = []
        for d in range(6, -1, -1):
            day = today - timedelta(days=d)
            next_day = day + timedelta(days=1)
            count = sess.query(Message).filter(Message.created_at >= day, Message.created_at < next_day).count()
            daily.append({'date': day.strftime('%m-%d'), 'count': count})
        return jsonify({
            'hourly': hourly,
            'daily': daily,
            'total_users': sess.query(User).count(),
            'total_messages': sess.query(Message).count()
        })
    finally:
        sess.close()
