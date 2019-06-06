import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db_setup import Base, Restaurant, MenuItem
from flask import Flask, request, render_template, redirect, url_for, jsonify
from waitress import serve

app = Flask(__name__)
engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine


def start():
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    return session


def close(session):
    session.close()

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
    serve(app, port=port)
