from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from flask_marshmallow import Marshmallow
from marshmallow import ValidationError, fields
from datetime import datetime
from typing import List
from sqlalchemy import select, delete 



app = Flask(__name__) #creates an instance of our flask application.
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:6811366Kk!@localhost/ecommerce_api'

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(app, model_class=Base)
ma = Marshmallow(app)


class Customer(Base):
    __tablename__ = 'Customer'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(100), nullable=False)
    email: Mapped[str] = mapped_column(db.String(200))
    adress: Mapped[str] = mapped_column(db.String(200))
    orders: Mapped[list["Orders"]] = db.relationship('Orders', back_populates='customer')
 
order_products = db.Table(
    "Order_Products", 
    Base.metadata, # Allows this table to locate the foreign keys from the other base class.
    db.Column('order_id', db.ForeignKey('Orders.id')),
    db.Column('product_id', db.ForeignKey('Products.id'))
)   

class Orders(Base):
    __tablename__ = 'Orders'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    order_date: Mapped[date] = mapped_column(db.Date, nullable=False)
    customers_id: Mapped[int] = mapped_column(db.ForeignKey('Customer.id'))
    # Creates a one- to many relationship to the customer table.
    customer: Mapped['Customer'] = db.relationship('Customer', back_populates='orders')
    products: Mapped[list['Products']] = db.relationship('Products', secondary=order_products, back_populates="orders")
    
    
    
class Products(Base):
    __tablename__ = 'Products'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    product_name: Mapped[str] = mapped_column(db.String(200), nullable=False)
    price: Mapped[float] = mapped_column(db.Float, nullable=False)
    orders: Mapped[list['Orders']] = db.relationship('Orders', secondary=order_products, back_populates="products")
    
#=========================Schema====================================


class CustomerSchema(ma.SQLAlchemyAutoSchema): 
    class Meta:
        model = Customer

class ProductSchema(ma.SQLAlchemyAutoSchema):
    class meta:
        model = Products
        
class OrderSchema(ma.SQLAlchemyAutoSchema):
    class meta:
        model = Orders
        include_fk = True

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)

product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)


#========================= API Route ====================================

@app.route('/')
def home():
    return "Home"

# Get all cutomers using a GET method.

@app.route("/customers", methods=['GET'])
def get_customers():
    query = select(Customer)
    result = db.session.execute(query).scalars()
    customers = result.all()
    return customers_schema.jsonify(customers)

#=====GET /users/<id>: Retrieve a user by ID=======
@app.route('/customers/<int:id>', methods=['GET'])
def get_user(id):
    user = db.session.get(Customer, id)
    return customers_schema.jsonify(user), 200



#========POST /users: Create a new user=========
@app.route("/customers", methods=['POST'])
def add_customer():
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    new_customer = Customer(name=customer_data['name'], email=customer_data['email'], address=customer_data['address'])
    db.session.add(new_customer)
    db.session.commit()
    
    return jsonify({"Message": "New customer added successfully",
                    "customer": customer_schema.dump(new_customer)}), 201


#=====PUT /users/<id>: Update a user by ID=====
@app.route('/customers/<int:id>', methods=['PUT'])
def update_customers(id):
    customers = db.session.get(Customer, id)
    
    if not customers:
        return jsonify({"message": "invalid user id"}), 400
    
    try:
        customers_data = customers_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    customers.name = customers_data['name']
    customers.email = customers_data['email']
    
    db.session.commit()
    return customers_schema.jsonify(customer), 200 
    
    
    
#======DELETE /users/<id>: Delete a user by ID========
@app.route('/customers/<int:id>', methods=['DELETE'])
def delete_customers(id):
    customers = db.session.get(Customer, id)
    
    if not customers:
        return jsonify({"message": "Invalid user id"}), 400
    
    db.session.delete(customers)
    db.session.commit()
    return jsonify({"message": f"succefully deleted customer {id}"}), 200



#========GET /products: Retrieve all products==========
@app.route('/products', methods=['GET'])
def get_products():
    products = Products.query.all()
    return jsonify(products_schema.dump(products))


#==========POST /products: Create a new product========
@app.route('/products', methods=['POST'])
def create_product():
    data = request.json
    new_product = Products(product_name=data['product_name'], price=data['price'])
    db.session.add(new_product)
    db.session.commit()
    return jsonify(product_schema.dump(new_product)), 201



#==========PUT /products/<id>: Update a product by ID===========
@app.route('/products/<int:id>', methods=['PUT'])
def update_products(id):
    products = db.session.get(Products, id)
    
    if not products:
        return jsonify({"message": "invalid product id"}), 400
    
    try:
        products_data = products_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    products.product_name = products_data['product_name']
    products.price = products_data['price']
    
    db.session.commit()
    
#=======DELETE /products/<id>: Delete a product by ID=======
@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    products = db.session.get(Products, id)
    
    if not products:
        return jsonify({"message": "Invalid product id"}), 400
    
    db.session.delete(products)
    db.session.commit()
    return jsonify({"message": f"succefully deleted product {id}"}), 200


#========POST /orders: Create a new order (requires user ID and order date)=======
@app.route('/orders', methods=['POST'])
def create_order():
    data = request.json
    new_order = Orders(customers_id=data['user_id'], order_date=datetime.utcnow().date())
    db.session.add(new_order)
    db.session.commit()
    return jsonify(order_schema.dump(new_order)), 201


#=======DELETE /orders/<order_id>/remove_product/<product_id>: Remove a product from an order=======
@app.route('/orders/<int:order_id>/remove_product/<int:product_id>', methods=['DELETE'])
def remove_product_from_order(order_id, product_id):
    order = Orders.query.filter_by(id=order_id).first()
    product = Products.query.filter_by(id=product_id).first()
    if product not in order.products:
        return jsonify({'message': 'Product not in order'}), 400
    order.products.remove(product)
    db.session.commit()
    return jsonify({'message': 'Product removed from order'})


#=======GET /orders/user/<user_id>: Get all orders for a user========
@app.route('/orders/user/<int:user_id>', methods=['GET'])
def get_orders_for_user(user_id):
    orders = Orders.query.filter_by(user_id=user_id).all()
    return jsonify(orders_schema.dump(orders))


#=======GET /orders/<order_id>/products: Get all products for an order==========
@app.route('/orders/<int:order_id>/products', methods=['GET'])
def get_products_for_order(order_id):
    order = db.session.get(Orders, order_id)
    return jsonify(products_schema.dump(order.products))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  
    app.run(debug=True)

    









































