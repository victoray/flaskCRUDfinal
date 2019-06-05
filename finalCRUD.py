from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db_setup import Base, Restaurant, MenuItem
from flask import Flask, request, render_template

app = Flask(__name__)
engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine


def start():
    DBSession = sessionmaker(bind=engine)
    return DBSession()


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
    return "new Restaurant"


@app.route('/<int:restaurant_id>/edit', methods=['GET', 'POST'])
def editrestaurant(restaurant_id):
    return "edit Restaurant"


@app.route('/<int:restaurant_id>/delete', methods=['GET', 'POST'])
def deleterestaurant(restaurant_id):
    return "delete Restaurant"


@app.route('/<int:restaurant_id>/')
def menu(restaurant_id):
    session = start()
    restaurant = session.query(Restaurant).filter(Restaurant.id == restaurant_id).one()
    menu = session.query(MenuItem).filter(MenuItem.restaurant_id == restaurant_id)
    for item in menu:
        print(item.course)
    close(session)
    return render_template('menu.html', restaurant=restaurant, menu=menu)


@app.route('/<int:restaurant_id>/new', methods=['GET', 'POST'])
def newmenu(restaurant_id):
    return "new Menu"


@app.route('/<int:restaurant_id>/<int:menu_id>/edit', methods=['GET', 'POST'])
def editmenu(restaurant_id, menu_id):
    return "edit Menu"


@app.route('/<int:restaurant_id>/<int:menu_id>/delete', methods=['GET', 'POST'])
def deletemenu(restaurant_id, menu_id):
    return "delete Menu"


if __name__ == '__main__':
    app.debug = True
    app.run(host="localhost", port=9000)
