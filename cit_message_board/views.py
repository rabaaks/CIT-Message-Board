import json
from io import BytesIO
from flask import Blueprint, flash, g, redirect, render_template, request, url_for, send_file, jsonify
from werkzeug.exceptions import abort

from .auth import login_required
from .db import get_db

bp = Blueprint('views', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/admin')
@login_required
def admin():
    db = get_db()
    posts = db.execute(
        'SELECT * FROM post'
    ).fetchall()
    return render_template('admin.html', posts=posts)

@bp.route('/add', methods=('GET', 'POST'))
def add():
    if request.method == 'POST':
        name = request.form['name']
        title = request.form['title']
        image = request.files['image']
        data = image.read()

        db = get_db()
        db.execute(
            'INSERT INTO post (title, author, data) VALUES (?, ?, ?)',
            (title, name, data)
        )
        db.commit()

    return render_template('add.html')

@bp.route('/live')
def live():
    return render_template('live.html')

@bp.route('/posts')
def posts():
    db = get_db()
    posts = db.execute(
        'SELECT id FROM post WHERE NOT admin_id IS NULL'
    ).fetchall()
    return jsonify([row['id'] for row in posts])

@bp.route('/images/<int:id>')
def images(id):
    db = get_db()
    file = db.execute(
        'SELECT data FROM post WHERE id = ?',
        (id,)
    ).fetchone()['data']
    return send_file(BytesIO(file), download_name='image.png')

@bp.route('/approve/<int:id>', methods=('POST',))
@login_required
def approve(id):
    db = get_db()
    db.execute(
        'UPDATE post SET admin_id = ? WHERE id = ?',
        (g.user['id'], id)
    )
    db.commit()

    return redirect(url_for('views.admin'))

@bp.route('/delete/<int:id>', methods=('POST',))
@login_required
def delete(id):
    db = get_db()
    db.execute(
        'DELETE FROM post WHERE id = ?',
        (id,)
    )
    db.commit()

    return redirect(url_for('views.admin'))