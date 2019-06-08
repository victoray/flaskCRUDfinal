import os

import httplib2
import requests
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db_setup import Base, Restaurant, MenuItem
from flask import Flask, request, render_template, redirect, url_for, jsonify, session as login_session, make_response, \
    abort, flash
from waitress import serve
import random, string, json



app = Flask(__name__)
engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine
CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']

def start():
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    return session


def close(session):
    session.close()

@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    print("TEST 1")
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
    print(access_token)
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

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
        print
        "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('sub')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['sub'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    print(data)
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print(output)
    return output

@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print ('Access Token is None')
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print('In gdisconnect access token is %s', access_token)
    print ('User name is: ')
    print (login_session['username'])
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print ('result is ')
    print (result)
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['sub']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    print("TEST 0")
    return render_template('login.html', STATE=state)

#Home Page
@app.route('/')
def home():
    session = start()
    restaurants = session.query(Restaurant).all()
    close(session)
    return render_template("index.html", restaurants=restaurants)

#New Restaurant
@app.route('/new', methods=['GET', 'POST'])
def newrestaurant():
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    session = start()

    if request.method == 'POST':
        restaurant = Restaurant(name=request.form['name'])
        session.add(restaurant)
        session.commit()
        return redirect(url_for('home'))

    close(session)
    return redirect("/#new-restaurant")

#Edit Restaurant
@app.route('/<int:restaurant_id>/edit', methods=['GET', 'POST'])
def editrestaurant(restaurant_id):
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    session = start()
    restaurant = session.query(Restaurant).filter(Restaurant.id == restaurant_id).one()

    if request.method == 'POST':
        restaurant.name = request.form['name']
        session.commit()
        close(session)
        return redirect(url_for('home'))
    close(session)
    return render_template('editrestaurant.html', restaurant=restaurant)

#Delete Restaurant
@app.route('/<int:restaurant_id>/delete', methods=['GET', 'POST'])
def deleterestaurant(restaurant_id):
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    session = start()
    restaurant = session.query(Restaurant).filter(Restaurant.id == restaurant_id).one()

    if request.method == 'POST':
        session.delete(restaurant)
        session.commit()
        close(session)
        return redirect(url_for('home'))

    close(session)
    return render_template('deleterestaurant.html', restaurant=restaurant)

# Menu View
@app.route('/<int:restaurant_id>/')
def menu(restaurant_id):
    session = start()
    restaurant = session.query(Restaurant).filter(Restaurant.id == restaurant_id).one()
    menu = session.query(MenuItem).filter(MenuItem.restaurant_id == restaurant_id).all()

    close(session)
    return render_template('menu.html', restaurant=restaurant, menu=menu)

#New Menu Item
@app.route('/<int:restaurant_id>/new', methods=['GET', 'POST'])
def newmenu(restaurant_id):
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    session = start()

    if request.method == 'POST':
        menuitem = MenuItem(name=str(request.form['name']).title(), price=request.form['price'],
                            description=request.form['description'], course=request.form['course'],
                            restaurant_id=restaurant_id)
        session.add(menuitem)
        session.commit()
        close(session)
        return redirect(url_for('menu', restaurant_id=restaurant_id))

    close(session)
    return render_template('newmenu.html', restaurant_id=restaurant_id)

#Edit menu
@app.route('/<int:restaurant_id>/<int:menu_id>/edit', methods=['GET', 'POST'])
def editmenu(restaurant_id, menu_id):
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    session = start()

    restaurant = session.query(Restaurant).filter(Restaurant.id == restaurant_id).one()
    menuitem = session.query(MenuItem).filter(MenuItem.id == menu_id).one()

    if request.method == 'POST':
        menuitem.name = str(request.form['name']).title()
        menuitem.price = request.form['price']
        menuitem.description = request.form['description']
        menuitem.course = request.form['course']
        session.commit()
        close(session)
        return redirect(url_for('menu', restaurant_id=restaurant_id))

    close(session)
    return render_template('editmenu.html', restaurant=restaurant, menuitem=menuitem)

#delete User
@app.route('/<int:restaurant_id>/<int:menu_id>/delete', methods=['GET', 'POST'])
def deletemenu(restaurant_id, menu_id):
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    session = start()
    menuitem = session.query(MenuItem).filter(MenuItem.id == menu_id).one()

    if request.method == 'POST':
        session.delete(menuitem)
        session.commit()
        close(session)
        return redirect(url_for('menu', restaurant_id=restaurant_id))

    close(session)
    return render_template('deletemenu.html', restaurant_id=restaurant_id, menuitem=menuitem)

@app.route('/<int:restaurant_id>/menu/JSON')
def restaurantMenuJSON(restaurant_id):
    session = start()
    items = session.query(MenuItem).filter_by(restaurant_id=restaurant_id).all()
    close(session)
    return jsonify(MenuItems=[i.serialize for i in items])


@app.route('/<int:restaurant_id>/menu/<int:menu_id>/JSON')
def menuJSON(restaurant_id, menu_id):
    session = start()
    menuitem = session.query(MenuItem).filter(MenuItem.id == menu_id).one()
    close(session)
    return jsonify(Menu=menuitem.serialize)

if __name__ == '__main__':
    app.secret_key = os.urandom(16)
    print(app.secret_key)
    port = int(os.environ.get('PORT', 8000))
    print(port)
    app.debug = True
    app.run(host='localhost', port=port)
