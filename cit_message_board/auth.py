import functools

import click
from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM admin WHERE username = ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('views.admin'))

        flash(error)

    return render_template('login.html')

def add_admin(username, password):
    db = get_db()

    try:
        db.execute(
            "INSERT INTO admin (username, password) VALUES (?, ?)",
            (username, generate_password_hash(password))
        )
        db.commit()

    except db.IntegrityError:
        return False

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('views.index'))

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM admin WHERE id = ?',
            (user_id,)
        ).fetchone()

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view

@click.command('add-admin')
@click.option('--username')
@click.option('--password')
def add_admin_command(username, password):
    """Add a new admin user."""
    if add_admin(username, password):
        click.echo('Username already exists.')
    else:
        click.echo(f'Added {username}: {password}.')

def init_app(app):
    app.cli.add_command(add_admin_command)