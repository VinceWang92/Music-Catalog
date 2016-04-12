from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker, scoped_session
from database_setup_catalog import Base, User, Genre, Song
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Music Catalog Application"


# Connect to Database and create database session
engine = create_engine('sqlite:///catalogwithusers.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(
        random.choice(string.ascii_uppercase + string.digits) for x in range(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code, now compatible with Python3
    
#    request.get_data()
    code = request.data.decode('utf-8')

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    # Submit request, parse response - Python3 compatible
    h = httplib2.Http()
    response = h.request(url, 'GET')[1]
    str_response = response.decode('utf-8')
    result = json.loads(str_response)

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    return output

# User Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    print "&"
    print newUser
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    print user.id
    print user.email
    return user.id


def getUserInfo(user_id):
    users = session.query(User).all()
    for item in users:
        print item.id
        print item.name

    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

# DISCONNECT - Revoke a current user's token and reset their login_session


@app.route('/gdisconnect')
def gdisconnect():
        # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# JSON APIs to view Restaurant Information
@app.route('/genre/<int:genre_id>/JSON')
def genreSongJSON(genre_id):
    genre = Genre.query.filter_by(id = genre_id).one()
    items = Song.query.filter_by(genre_id=genre_id).all()
    return jsonify(Genre=[i.serialize for i in items])


@app.route('/genre/<int:genre_id>/list/<int:song_id>/JSON')
def songJSON(genre_id, song_id):
    song = Song.query.filter_by(id=genre_id).one()
    return jsonify(Song=song.serialize)


@app.route('/genre/JSON')
def genresJSON():
    genres = Genre.query.all()
    return jsonify(Genres=[r.serialize for r in genres])

# http://docs.sqlalchemy.org/en/rel_0_8/orm/session.html#sqlalchemy.orm.scoping.scoped_session
db_session = scoped_session(sessionmaker(autocommit=False,
    autoflush=False,
    bind=engine))

Base.query = db_session.query_property()

# Show all catalog of music genre
@app.route('/')
@app.route('/catalog/')
def showCatalog():
    genres = Genre.query.all()
    songs = Song.query.order_by(Song.created.desc()).all()
    if 'username' not in login_session:
        return render_template('publicCatalog.html', genres=genres)
    else:
        return render_template('catalog.html', genres=genres, username = login_session['username'])

# Create a new genre


@app.route('/genre/new/', methods=['GET', 'POST'])
def newGenre():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newGenre = Genre(
            name=request.form['name'], user_id=login_session['user_id'])
        session.add(newGenre)
        flash('New Genre %s Successfully Created' % newGenre.name)
        session.commit()
        return redirect(url_for('showCatalog'))
    else:
        return render_template('newGenre.html', username = login_session['username'])

# Edit a genre


@app.route('/genre/<int:genre_id>/edit/', methods=['GET', 'POST'])
def editGenre(genre_id):
    editedGenre = Genre.query.filter_by(id=genre_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if editedGenre.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to edit this Genre. Please create your own Genre in order to edit.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            editedGenre.name = request.form['name']
            flash('Genre Successfully Edited %s' % editedGenre.name)
            return redirect(url_for('showCatalog'))
    else:
        return render_template('editGenre.html', genre=editedGenre, username = login_session['username'])


# Delete a genre
@app.route('/genre/<int:genre_id>/delete/', methods=['GET', 'POST'])
def deleteGenre(genre_id):
    genreToDelete = Genre.query.filter_by(id=genre_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if genreToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to delete this Genre. Please create your own Genre in order to delete.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        print "%"
        db_session.delete(genreToDelete)
        print "$"
        flash('%s Successfully Deleted' % genreToDelete.name)
        db_session.commit()
        return redirect(url_for('showCatalog', genre_id=genre_id))
    else:
        return render_template('deleteGenre.html', genre=genreToDelete, username = login_session['username'])

# Show a Genre list


@app.route('/catalog/<int:genre_id>/')
@app.route('/catalog/<int:genre_id>/list/')
def showGenre(genre_id):
    genre = Genre.query.filter_by(id=genre_id).one()
    creator = getUserInfo(genre.user_id)
    songs = Song.query.filter_by(genre=genre).all()
    if 'username' not in login_session or creator.id != login_session['user_id']:
        return render_template('publicGenre.html', songs=songs, genre=genre, creator=creator, flag = 0)
    else:
        return render_template('genre.html', songs=songs, genre=genre, creator=creator, username = login_session['username'])


# Create a new song
@app.route('/catalog/<int:genre_id>/list/new/', methods=['GET', 'POST'])
def newSong(genre_id):
    if 'username' not in login_session:
        return redirect('/login')
    genre = Genre.query.filter_by(id=genre_id).one()
    if login_session['user_id'] != genre.user_id:
        return "<script>function myFunction() {alert('You are not authorized to add Songs to this genre. Please create your own genre in order to add items.');}</script><body onload='myFunction()''>"
    else:
        if request.method == 'POST':
            newSong = Song(name=request.form['name'], description=request.form['description'], url=request.form[
                               'url'], artist=request.form['artist'], genre_id=genre_id, owner_id=genre.user_id)
            session.add(newSong)
            session.commit()
            flash('New Genre %s Song Successfully Created' % (newSong.name))
            return redirect(url_for('showGenre', genre_id=genre_id))

    return render_template('newSong.html', genre_id=genre_id)

# Edit an existing song


@app.route('/catalog/<int:genre_id>/list/<int:song_id>/edit', methods=['GET', 'POST'])
def editSong(genre_id, song_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedSong = Song.query.filter_by(id=song_id).one()
    genre = Genre.query.filter_by(id=genre_id).one()
    if login_session['user_id'] != genre.user_id:
        return "<script>function myFunction() {alert('You are not authorized to edit Songs to this genre. Please create your own genre in order to edit items.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            editedSong.name = request.form['name']
        if request.form['description']:
            editedSong.description = request.form['description']
        if request.form['url']:
            editedSong.url = request.form['url']
        if request.form['artist']:
            editedSong.artist = request.form['artist']
        db_session.add(editedSong)
        db_session.commit()
        flash('Song Successfully Edited')
        return redirect(url_for('showGenre', genre_id=genre_id))
    else:
        return render_template('editSong.html', genre_id=genre_id, song_id=song_id, song=editedSong)


# Delete a song
@app.route('/catalog/<int:genre_id>/list/<int:song_id>/delete', methods=['GET', 'POST'])
def deleteSong(genre_id, song_id):
    if 'username' not in login_session:
        return redirect('/login')
    genre = Genre.query.filter_by(id=genre_id).one()
    songToDelete = Song.query.filter_by(id=song_id).one()
    if login_session['user_id'] != genre.user_id:
        return "<script>function myFunction() {alert('You are not authorized to delete Songs to this genre. Please create your own genre in order to delete Songs.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        db_session.delete(songToDelete)
        db_session.commit()
        flash('Genre Song Successfully Deleted')
        return redirect(url_for('showGenre', genre_id=genre_id))
    else:
        return render_template('deleteSong.html', song=songToDelete)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
