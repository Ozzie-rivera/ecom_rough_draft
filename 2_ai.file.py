from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import mysql.connector
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:<YOUR PASSWORD>@localhost/ecommerce_api'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    orders = db.relationship('Order', backref='user', lazy=True)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    products = db.relationship('Product', secondary='order_product', backref='orders')

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(80), nullable=False)
    price = db.Column(db.Float, nullable=False)

order_product = db.Table('order_product',
    db.Column('order_id', db.Integer, db.ForeignKey('order.id'), primary_key=True),
    db.Column('product_id', db.Integer, db.ForeignKey('product.id'), primary_key=True)
)

# Marshmallow Schemas
class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        include_fk = True

class OrderSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Order
        include_fk = True

class ProductSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Product

user_schema = UserSchema()
users_schema = UserSchema(many=True)
order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

# User Endpoints
@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify(users_schema.dump(users))

@app.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    user = User.query.get_or_404(id)
    return jsonify(user_schema.dump(user))

@app.route('/users', methods=['POST'])
def create_user():
    data = request.json
    new_user = User(name=data['name'], address=data['address'], email=data['email'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify(user_schema.dump(new_user)), 201

@app.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    data = request.json
    user = User.query.get_or_404(id)
    user.name = data.get('name', user.name)
    user.address = data.get('address', user.address)
    user.email = data.get('email', user.email)
    db.session.commit()
    return jsonify(user_schema.dump(user))

@app.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted'})

# Product Endpoints
@app.route('/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify(products_schema.dump(products))

@app.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    product = Product.query.get_or_404(id)
    return jsonify(product_schema.dump(product))

@app.route('/products', methods=['POST'])
def create_product():
    data = request.json
    new_product = Product(product_name=data['product_name'], price=data['price'])
    db.session.add(new_product)
    db.session.commit()
    return jsonify(product_schema.dump(new_product)), 201

@app.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    data = request.json
    product = Product.query.get_or_404(id)
    product.product_name = data.get('product_name', product.product_name)
    product.price = data.get('price', product.price)
    db.session.commit()
    return jsonify(product_schema.dump(product))

@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': 'Product deleted'})

# Order Endpoints
@app.route('/orders', methods=['POST'])
def create_order():
    data = request.json
    new_order = Order(user_id=data['user_id'], order_date=datetime.utcnow())
    db.session.add(new_order)
    db.session.commit()
    return jsonify(order_schema.dump(new_order)), 201

@app.route('/orders/<int:order_id>/add_product/<int:product_id>', methods=['PUT'])
def add_product_to_order(order_id, product_id):
    order = Order.query.get_or_404(order_id)
    product = Product.query.get_or_404(product_id)
    if product in order.products:
        return jsonify({'message': 'Product already in order'}), 400
    order.products.append(product)
    db.session.commit()
    return jsonify({'message': 'Product added to order'})

@app.route('/orders/<int:order_id>/remove_product/<int:product_id>', methods=['DELETE'])
def remove_product_from_order(order_id, product_id):
    order = Order.query.get_or_404(order_id)
    product = Product.query.get_or_404(product_id)
    if product not in order.products:
        return jsonify({'message': 'Product not in order'}), 400
    order.products.remove(product)
    db.session.commit()
    return jsonify({'message': 'Product removed from order'})

@app.route('/orders/user/<int:user_id>', methods=['GET'])
def get_orders_for_user(user_id):
    orders = Order.query.filter_by(user_id=user_id).all()
    return jsonify(orders_schema.dump(orders))

@app.route('/orders/<int:order_id>/products', methods=['GET'])
def get_products_for_order(order_id):
    order = Order.query.get_or_404(order_id)
    return jsonify(products_schema.dump(order.products))

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
