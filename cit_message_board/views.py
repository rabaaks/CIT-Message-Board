import json
from datetime import datetime
from io import BytesIO
from flask import Blueprint, flash, g, redirect, render_template, request, url_for, send_file, jsonify
from werkzeug.exceptions import abort
import pytz

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
        'SELECT created, begins, expires, title, author, admin_id, id FROM post'
    ).fetchall()
    return render_template('admin.html', posts=posts)

@bp.route('/add', methods=('GET', 'POST'))
def add():
    if request.method == 'POST':
        name = request.form['name']
        title = request.form['title']

        created = datetime.now().strftime('%Y-%m-%dT%H:%M')

        # Convert the time given by the user into UTC time
        deeprun_time = pytz.timezone('US/Eastern')
        utc = pytz.timezone('UTC')

        begins = deeprun_time.localize(datetime.strptime(request.form['begins'], '%Y-%m-%dT%H:%M')).astimezone(utc).strftime('%Y-%m-%dT%H:%M')
        expires = deeprun_time.localize(datetime.strptime(request.form['expires'], '%Y-%m-%dT%H:%M')).astimezone(utc).strftime('%Y-%m-%dT%H:%M')

        image = request.files['image'].read()

        db = get_db()
        db.execute(
            'INSERT INTO post (created, begins, expires, title, author, data) VALUES (?, ?, ?, ?, ?, ?)',
            (created, begins, expires, title, name, image)
        )
        db.commit()

    return render_template('add.html')

@bp.route('/live')
def live():
    return render_template('live.html')

@bp.route('/posts')
def posts():
    # Used by the front end to get a list of posts to cycle through
    db = get_db()
    # If the admin id is null it hasn't been approved
    posts = db.execute(
        'SELECT id, begins, expires FROM post WHERE NOT admin_id IS NULL'
    ).fetchall()
    filtered_posts = []
    for post in posts:
        id = post['id']
        current_time = datetime.now()
        begin_time = datetime.strptime(post['begins'], '%Y-%m-%dT%H:%M')
        expire_time = datetime.strptime(post['expires'], '%Y-%m-%dT%H:%M')
        print(begin_time)
        print(expire_time)
        if begin_time > current_time:
            continue
        elif expire_time < current_time:
            db.execute(
                'DELETE FROM post WHERE id = ?',
                (id,)
            )
            db.commit()
            continue

        filtered_posts.append(id)

    return jsonify(filtered_posts)

@bp.route('/images/<int:id>')
def images(id):
    # Used to get an image in a displayable format
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