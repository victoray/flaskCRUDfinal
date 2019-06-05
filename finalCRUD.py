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
    return "hello"


@app.route('/new', methods=['GET', ['POST']])
def newrestaurant():
    return "new Restaurant"


@app.route('/<int:restaurant_id>/edit', methods=['GET', ['POST']])
def editrestaurant(restaurant_id):
    return "edit Restaurant"


@app.route('/<int:restaurant_id>/delete', methods=['GET', ['POST']])
def deleterestaurant(restaurant_id):
    return "delete Restaurant"


@app.route('/<int:restaurant_id>/')
def menu(restaurant_id):
    return "Menu"


@app.route('/<int:restaurant_id>/new', methods=['GET', ['POST']])
def newmenu(restaurant_id):
    return "new Menu"


@app.route('/<int:restaurant_id>/<int:menu_id>/edit', methods=['GET', ['POST']])
def editmenu(restaurant_id, menu_id):
    return "edit Menu"


@app.route('/<int:restaurant_id>/<int:menu_id>/delete', methods=['GET', ['POST']])
def deletemenu(restaurant_id, menu_id):
    return "delete Menu"


if __name__ == '__main__':
    app.debug = True
    app.run(host="localhost", port=9000)
