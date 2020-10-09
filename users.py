from flask import Flask
from flask import Flask, request, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
# app.config.from_envvar('APP_CONFIG')

def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect('users.db')
        db.row_factory = make_dicts
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


@app.cli.command('init')
def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('microservices.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.route('/userlist', methods=['GET'])
def users_all():
    all_users = query_db('SELECT * FROM users;')
    return jsonify(all_users)

@app.route('/users', methods=['POST'])
def createUser():
    try:
        query_params = request.get_json()
        username = query_params['username']
        password = query_params['password']
        password = generate_password_hash(password)
        email = query_params['email']
        db = get_db()
        query_db('INSERT INTO users(username,password,email) VALUES (?,?,?);',(username,password,email))
        db.commit()
        response = jsonify({"status": "created" })
        response.status_code = 201
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        return response
    except Exception:
        response = jsonify({"status": "Bad request" })
        response.status_code = 400
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        return response