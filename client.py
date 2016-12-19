#!/usr/bin/env python3
# coding=utf-8
from flask import Flask, session, redirect, url_for, request, render_template, g, abort
from flask_httpauth import HTTPBasicAuth
from random import choice
from string import ascii_letters
from datetime import datetime as dtime

from client_libs import Actor, NotAuthedError

__uri_public__ = 'https://{}:{}@endtropie.mooo.com/api/v2/{}'
__uri_dev__ = 'https://{}:{}@localhost:4444/api/v2/{}'
__uri__ = __uri_public__

new_user = {
    'name': "test-" + "".join([choice(ascii_letters).upper() for x in range(20)]),
    'fullname': "test",
    'email': "test@mail.com",
    'group': "user",
    'rank': 10
}

app = Flask(__name__)
auth = HTTPBasicAuth(app)


@auth.login_required
@app.route('/users')
def get_users():
    def make_view():
        actor = make_actor(session)
        data, status = actor.request_all()
        session.update({'token': actor.token})
        results = data['result']['users']
        list_of_users = [
            user
            for user
            in results.values()
            ]
        return render_template(
            'show_users.html',
            users=list_of_users
        )

    if 'username' in session:
        try:
            return make_view()
        except NotAuthedError:
            return redirect(url_for('login'))

    else:
        return redirect(url_for('login'))


@auth.login_required
@app.route('/users/<string:username>')
def get_user_by_name(username=None):
    def make_view():
        actor = make_actor(session)
        data, status = actor.get_user(username)
        session.update({'token': actor.token})
        result = data['result']['user']

        return render_template(
            'show_user.html',
            user=result
        )

    if 'username' in session:
        try:
            username = username or session['username']
            return make_view()
        except NotAuthedError:
            return redirect(url_for('login'))

    else:
        return redirect(url_for('login'))


@auth.login_required
@app.route('/')
@app.route('/users/self')
def self():
    def make_view():
        actor = make_actor(session)
        username = session['username']
        data, status = actor.get_user(username)
        session.update({'token': actor.token})
        result = data['result']['user']
        friends = result['friends']
        creation = dtime(**result['creation_time'])

        return render_template(
            'self.html',
            user=result,
            friends=friends,
            creation=creation
        )

    if 'username' in session:
        try:
            return make_view()
        except NotAuthedError:

            return redirect(url_for('login'))

    else:
        return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    def initial_token():
        actor = make_actor(session)
        try:
            actor.get_token()
            session.update({'token': actor.token})
        except NotAuthedError as nae:
            print("shit!!!")
            raise nae

    if request.method == 'POST':
        session.update(
            {'username': request.form['username'],
             'password': request.form['password']}
        )
        initial_token()
        return redirect(url_for('self'))

    elif request.method == 'GET':
        return render_template('login.html')
    else:
        abort(405)


@auth.login_required
@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('password', None)
    session.pop('token', None)
    return redirect(url_for('login'))


@app.before_request
def before_request():
    if 'token' not in session:
        if 'username' in session:
            print("we have no token but a user, so lets get a token")


def make_actor(session, ressource="users"):
    args = {'ressource': ressource}
    if 'username' in session:
        args.update(
            {'username': session['username'],
             'password': session['password']})
    if 'token' in session:
        args.update({'token': session['token']})

    return Actor(__uri__, **args)


def dict_to_vars(_dict):
    if 'user' in _dict:

        return



app.secret_key = """+\xf0\xbb;IZ\xb58\xd9\xde\x7f%`\xe1\xa2\xc3\xa9\xa3\x96N\xa9s\x12x,\x0fkL\x111\x11\xa1"""
context = (
    'certs/broker_client.crt',
    'certs/broker_client.key'
)

if __name__ == "__main__":
    app.run(
        host='0.0.0.0',
        port=4445,
        threaded=True,
        debug=True,
        ssl_context=context,
    )

