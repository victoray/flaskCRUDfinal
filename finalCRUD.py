from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db_setup import Base, Restaurant, MenuItem
from flask import Flask, request, render_template, redirect, url_for

app = Flask(__name__)
engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine


def start():
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    return session


def close(session):
    session.close()


@app.route('/')
def home():
    session = start()
    restaurants = session.query(Restaurant).all()
    close(session)
    return render_template("index.html", restaurants=restaurants)


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


@app.route('/<int:restaurant_id>/')
def menu(restaurant_id):
    session = start()
    restaurant = session.query(Restaurant).filter(Restaurant.id == restaurant_id).one()
    menu = session.query(MenuItem).filter(MenuItem.restaurant_id == restaurant_id).all()

    close(session)
    return render_template('menu.html', restaurant=restaurant, menu=menu)


@app.route('/<int:restaurant_id>/new', methods=['GET', 'POST'])
def newmenu(restaurant_id):
    return "new Menu"


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


if __name__ == '__main__':
    app.debug = True
    app.run(host="localhost", port=9000)
