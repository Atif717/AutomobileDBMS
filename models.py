from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# User Table
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)

# Vehicle Tables
class Vehicle(db.Model):
    __tablename__ = 'vehicle'
    vin = db.Column(db.String(20), primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'))
    model_id = db.Column(db.Integer, db.ForeignKey('model.id'))
    price = db.Column(db.Numeric(10, 2))
    color = db.Column(db.String(20))
    year = db.Column(db.Integer)

class Brand(db.Model):
    __tablename__ = 'brand'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))

class Model(db.Model):
    __tablename__ = 'model'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))

# Vehicle Options
class VehicleOption(db.Model):
    __tablename__ = 'vehicleoption'
    vin = db.Column(db.String(20), db.ForeignKey('vehicle.vin'), primary_key=True)
    option_id = db.Column(db.Integer, primary_key=True)
    install_date = db.Column(db.Date)
    option_status = db.Column(db.String(50))
    description = db.Column(db.String(100))

# Customer Tables
class Customer(db.Model):
    __tablename__ = 'customer'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    street = db.Column(db.String(100))
    city = db.Column(db.String(50))
    state = db.Column(db.String(20))
    zip_code = db.Column(db.String(10))

class CustomerPhoneNumber(db.Model):
    __tablename__ = 'customerphonenumbers'
    number = db.Column(db.String(50), primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))

# Dealer and Inventory
class Dealer(db.Model):
    __tablename__ = 'dealer'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    contact = db.Column(db.String(15))

class DealerLocation(db.Model):
    __tablename__ = 'dealerlocations'
    location = db.Column(db.String(50), primary_key=True)
    dealer_id = db.Column(db.Integer, db.ForeignKey('dealer.id'))

class Inventory(db.Model):
    __tablename__ = 'inventory'
    dealer_id = db.Column(db.Integer, db.ForeignKey('dealer.id'), primary_key=True)
    vin = db.Column(db.String(20), db.ForeignKey('vehicle.vin'), primary_key=True)
    stock_quantity = db.Column(db.Integer)
    stock_date = db.Column(db.Date)
    price_offered = db.Column(db.Numeric(10, 2))

# Employee
class Employee(db.Model):
    __tablename__ = 'employee'
    id = db.Column(db.Integer, primary_key=True)
    dealer_id = db.Column(db.Integer, db.ForeignKey('dealer.id'))
    name = db.Column(db.String(50))
    position = db.Column(db.String(50))
    salary = db.Column(db.Numeric(10, 2))
    contact = db.Column(db.String(15))
    supervisor_id = db.Column(db.Integer, db.ForeignKey('employee.id'))

# Sale and Service
class Sale(db.Model):
    __tablename__ = 'sale'
    vin = db.Column(db.String(20), db.ForeignKey('vehicle.vin'), primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), primary_key=True)
    price_sold = db.Column(db.Numeric(10, 2))
    payment_method = db.Column(db.String(20))
    warranty_period = db.Column(db.String(20))
    purchase_date = db.Column(db.Date)

class Service(db.Model):
    __tablename__ = 'service'
    vin = db.Column(db.String(20), db.ForeignKey('vehicle.vin'), primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), primary_key=True)
    service_id = db.Column(db.Integer, primary_key=True)
    service_date = db.Column(db.Date)
    service_detail = db.Column(db.String(100))
