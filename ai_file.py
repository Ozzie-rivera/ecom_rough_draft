from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from flask_marshmallow import Marshmallow
from marshmallow import ValidationError
from datetime import date
from typing import List
from sqlalchemy import select

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:<YOUR_PASSWORD>@localhost/ecommerce_api'

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(app, model_class=Base)
ma = Marshmallow(app)

class Customer(Base):
    __tablename__ = 'Customers'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(100), nullable=False)
    email: Mapped[str] = mapped_column(db.String(200))
    address: Mapped[str] = mapped_column(db.String(200))  # Fixed typo (was 'adress')
    orders: Mapped[List["Orders"]] = relationship('Orders', back_populates='customer')

order_products = db.Table(
    "Order_Products", 
    Base.metadata,
    db.Column('order_id', db.ForeignKey('Orders.id')),
    db.Column('product_id', db.ForeignKey('Products.id'))
)   

class Orders(Base):
    __tablename__ = 'Orders'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    order_date: Mapped[date] = mapped_column(db.Date, nullable=False)
    customer_id: Mapped[int] = mapped_column(db.ForeignKey('Customers.id'))  # Fixed Foreign Key name
    customer: Mapped["Customer"] = relationship('Customer', back_populates='orders')
    products: Mapped[List["Products"]] = relationship('Products', secondary=order_products, back_populates="orders")

class Products(Base):
    __tablename__ = 'Products'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    product_name: Mapped[str] = mapped_column(db.String(200), nullable=False)
    price: Mapped[float] = mapped_column(db.Float, nullable=False)
    orders: Mapped[List["Orders"]] = relationship('Orders', secondary=order_products, back_populates="products")

# ========================= Schema =========================

class CustomerSchema(ma.SQLAlchemyAutoSchema): 
    class Meta:
        model = Customer

class ProductSchema(ma.SQLAlchemyAutoSchema):
    class Meta:  # Fixed capitalization of Meta
        model = Products
        
class OrderSchema(ma.SQLAlchemyAutoSchema):
    class Meta:  # Fixed capitalization of Meta
        model = Orders
        include_fk = True

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)

product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)

# ========================= API Routes =========================

@app.route('/')
def home():
    return "Home"

@app.route("/customers", methods=['GET'])
def get_customers():
    query = select(Customer)
    result = db.session.execute(query).scalars()
    customers = result.all()
    return customers_schema.jsonify(customers)

@app.route("/customers", methods=['POST'])
def add_customer():
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400  # Fixed "e.message" → should be "e.messages"
    
    new_customer = Customer(name=customer_data['name'], email=customer_data['email'], address=customer_data['address'])
    db.session.add(new_customer)
    db.session.commit()
    
    return jsonify({
        "Message": "New customer added successfully",
        "customer": customer_schema.dump(new_customer)
    }), 201

if __name__ == '__main__':
    app.run(debug=True)
