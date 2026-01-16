import os
import sqlite3
from flask import Flask, g, redirect, render_template, request, url_for

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'app.db')


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    with open(os.path.join(BASE_DIR, 'schema.sql'), 'r', encoding='utf-8') as f:
        db.executescript(f.read())
    db.commit()
    db.close()


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-secret-key'
    app.teardown_appcontext(close_db)

    if not os.path.exists(DB_PATH):
        init_db()

    @app.route('/')
    def index():
        return redirect(url_for('list_canali'))

    @app.route('/canali')
    def list_canali():
        db = get_db()
        canali = db.execute('SELECT * FROM canali ORDER BY id DESC').fetchall()
        return render_template('canali.html', canali=canali)

    @app.route('/canali/nuovo', methods=('GET', 'POST'))
    def new_canale():
        error = None
        if request.method == 'POST':
            nome = request.form.get('nome', '').strip()
            numero_iscritti = request.form.get('numero_iscritti', '0').strip()
            categoria = request.form.get('categoria', '').strip()

            if not nome:
                error = 'Nome obbligatorio.'
            elif not categoria:
                error = 'Categoria obbligatoria.'
            else:
                try:
                    numero_iscritti_val = int(numero_iscritti) if numero_iscritti else 0
                except ValueError:
                    error = 'Numero iscritti non valido.'
                else:
                    db = get_db()
                    db.execute(
                        'INSERT INTO canali (nome, numero_iscritti, categoria) VALUES (?, ?, ?)',
                        (nome, numero_iscritti_val, categoria)
                    )
                    db.commit()
                    return redirect(url_for('list_canali'))

        return render_template('canale_form.html', error=error)

    def get_canale(canale_id):
        db = get_db()
        canale = db.execute('SELECT * FROM canali WHERE id = ?', (canale_id,)).fetchone()
        return canale

    @app.route('/canali/<int:canale_id>')
    def view_canale(canale_id):
        canale = get_canale(canale_id)
        if canale is None:
            return redirect(url_for('list_canali'))
        db = get_db()
        video = db.execute(
            'SELECT * FROM video WHERE canale_id = ? ORDER BY id DESC',
            (canale_id,)
        ).fetchall()
        return render_template('video.html', canale=canale, video=video)

    @app.route('/canali/<int:canale_id>/video/nuovo', methods=('GET', 'POST'))
    def new_video(canale_id):
        canale = get_canale(canale_id)
        if canale is None:
            return redirect(url_for('list_canali'))

        error = None
        if request.method == 'POST':
            titolo = request.form.get('titolo', '').strip()
            durata = request.form.get('durata', '').strip()
            immagine = request.form.get('immagine', '').strip()

            if not titolo:
                error = 'Titolo obbligatorio.'
            elif not durata:
                error = 'Durata obbligatoria.'
            else:
                try:
                    durata_val = int(durata)
                except ValueError:
                    error = 'Durata non valida.'
                else:
                    db = get_db()
                    db.execute(
                        'INSERT INTO video (canale_id, titolo, durata, immagine) VALUES (?, ?, ?, ?)',
                        (canale_id, titolo, durata_val, immagine if immagine else None)
                    )
                    db.commit()
                    return redirect(url_for('view_canale', canale_id=canale_id))

        return render_template('video_form.html', canale=canale, error=error)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
