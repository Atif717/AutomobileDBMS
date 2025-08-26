import os
from datetime import date
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
from models import db, User, Customer, Sale, Employee, Vehicle, Brand, Model, Dealer, Service, Inventory

app = Flask(__name__)

# --- Configuration for Deployment ---
# Use environment variables for sensitive data.
# Render will provide the DATABASE_URL. The SECRET_KEY you will set yourself.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://postgres:new_secure_password@localhost/automobileDBMS')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.environ.get('SECRET_KEY', 'a-super-secret-key-for-development')

db.init_app(app)
migrate = Migrate(app, db)

# --- Routes ---

@app.route('/')
def index():
    return render_template('login.html')

# --- Security Enhancement: Password Hashing ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        # Check if user exists and if the hashed password matches
        if user and check_password_hash(user.password, password):
            session['user'] = username
            session['role'] = user.role
            
            if user.role == 'Admin':
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'Dealer':
                dealer = Dealer.query.filter_by(name=user.username).first()
                if dealer:
                    return redirect(url_for('dealer_dashboard', dealer_id=dealer.id))
                else:
                    flash("Dealer profile not found.")
                    return redirect(url_for('login'))
            elif user.role == 'Customer':
                return redirect(url_for('customer_dashboard'))
            else:
                flash("Unknown role. Access denied.")
                return redirect(url_for('login'))
        else:
            flash("Invalid username or password.")
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form.get('role', 'Customer')

        if User.query.filter_by(username=username).first():
            flash('Username already exists!')
            return redirect(url_for('register'))

        # Hash the password before storing it
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password, role=role)
        
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully! Please login.')
        return redirect(url_for('login'))

    return render_template('register.html')

# --- Dashboards ---

@app.route('/admin')
def admin_dashboard():
    if 'role' in session and session['role'] == 'Admin':
        return render_template('admin_dashboard.html')
    return redirect(url_for('index'))

@app.route('/dealer/<int:dealer_id>')
def dealer_dashboard(dealer_id):
    if 'role' in session and session['role'] == 'Dealer':
        return render_template('dealer_dashboard.html', dealer_id=dealer_id)
    return redirect(url_for('index'))

@app.route('/customer')
def customer_dashboard():
    if 'role' in session and session['role'] == 'Customer':
        return render_template('customer_dashboard.html')
    return redirect(url_for('index'))

# --- Vehicle Management ---

@app.route('/vehicles', methods=['GET'])
def manage_vehicles():
    if 'role' in session and session['role'] == 'Admin':
        vehicles = Vehicle.query.all()
        return render_template('vehicles.html', vehicles=vehicles)
    return redirect(url_for('index'))

@app.route('/vehicles/add', methods=['GET', 'POST'])
def add_vehicle():
    if 'role' in session and session['role'] == 'Admin':
        if request.method == 'POST':
            vin = request.form['vin']
            brand_id = request.form['brand_id']
            model_id = request.form['model_id']
            price = request.form['price']
            color = request.form['color']
            year = request.form['year']
            try:
                new_vehicle = Vehicle(vin=vin, brand_id=brand_id, model_id=model_id, price=price, color=color, year=year)
                db.session.add(new_vehicle)
                db.session.commit()
                flash('Vehicle added successfully!')
                return redirect(url_for('manage_vehicles'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error: {str(e)}')
        brands = Brand.query.all()
        models = Model.query.all()
        return render_template('add_vehicle.html', brands=brands, models=models)
    return redirect(url_for('index'))

@app.route('/vehicles/edit/<vin>', methods=['GET', 'POST'])
def edit_vehicle(vin):
    if 'role' in session and session['role'] == 'Admin':
        vehicle = db.session.get(Vehicle, vin)
        if request.method == 'POST':
            vehicle.brand_id = request.form['brand_id']
            vehicle.model_id = request.form['model_id']
            vehicle.price = request.form['price']
            vehicle.color = request.form['color']
            vehicle.year = request.form['year']
            try:
                db.session.commit()
                flash('Vehicle updated successfully!')
                return redirect(url_for('manage_vehicles'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error: {str(e)}')
        brands = Brand.query.all()
        models = Model.query.all()
        return render_template('edit_vehicle.html', vehicle=vehicle, brands=brands, models=models)
    return redirect(url_for('index'))

@app.route('/vehicles/delete/<vin>', methods=['POST'])
def delete_vehicle(vin):
    if 'role' in session and session['role'] == 'Admin':
        try:
            vehicle = db.session.get(Vehicle, vin)
            db.session.delete(vehicle)
            db.session.commit()
            flash('Vehicle deleted successfully!')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}')
    return redirect(url_for('manage_vehicles'))

# --- Dealer Management ---

@app.route('/dealers')
def view_dealers():
    dealers = Dealer.query.all()
    return render_template('view_dealers.html', dealers=dealers)

@app.route('/dealers/add', methods=['GET', 'POST'])
def add_dealer():
    if request.method == 'POST':
        id = request.form['id']
        name = request.form['name']
        contact = request.form['contact']
        new_dealer = Dealer(id=id, name=name, contact=contact)
        db.session.add(new_dealer)
        db.session.commit()
        flash('Dealer added successfully!')
        return redirect(url_for('view_dealers'))
    return render_template('add_dealer.html')

@app.route('/dealers/edit/<int:id>', methods=['GET', 'POST'])
def edit_dealer(id):
    dealer = db.session.get(Dealer, id)
    if not dealer:
        flash('Dealer not found!')
        return redirect(url_for('view_dealers'))
    if request.method == 'POST':
        dealer.name = request.form['name']
        dealer.contact = request.form['contact']
        db.session.commit()
        flash('Dealer updated successfully!')
        return redirect(url_for('view_dealers'))
    return render_template('edit_dealer.html', dealer=dealer)

@app.route('/dealers/delete/<int:id>', methods=['POST'])
def delete_dealer(id):
    dealer = db.session.get(Dealer, id)
    if dealer:
        db.session.delete(dealer)
        db.session.commit()
        flash('Dealer deleted successfully!')
    else:
        flash('Dealer not found!')
    return redirect(url_for('view_dealers'))

# --- Customer Management ---

@app.route('/customers')
def view_customers():
    customers = Customer.query.all()
    return render_template('view_customers.html', customers=customers)

@app.route('/customers/add', methods=['GET', 'POST'])
def add_customer():
    if request.method == 'POST':
        customer_id = request.form['customer_id']
        name = request.form['name']
        street = request.form['street']
        city = request.form['city']
        state = request.form['state']
        zip_code = request.form['zip_code']
        new_customer = Customer(id=customer_id, name=name, street=street, city=city, state=state, zip_code=zip_code)
        db.session.add(new_customer)
        db.session.commit()
        flash('Customer added successfully!')
        return redirect(url_for('view_customers'))
    return render_template('add_customer.html')

@app.route('/customers/edit/<int:id>', methods=['GET', 'POST'])
def edit_customer(id):
    customer = db.session.get(Customer, id)
    if not customer:
        flash('Customer not found!')
        return redirect(url_for('view_customers'))
    if request.method == 'POST':
        customer.name = request.form['name']
        customer.street = request.form['street']
        customer.city = request.form['city']
        customer.state = request.form['state']
        customer.zip_code = request.form['zip_code']
        db.session.commit()
        flash('Customer updated successfully!')
        return redirect(url_for('view_customers'))
    return render_template('edit_customer.html', customer=customer)

@app.route('/customers/delete/<int:id>', methods=['POST'])
def delete_customer(id):
    customer = db.session.get(Customer, id)
    if customer:
        try:
            db.session.delete(customer)
            db.session.commit()
            flash('Customer deleted successfully!')
        except IntegrityError:
            db.session.rollback()
            flash('Error: This customer is referenced by other records (like sales) and cannot be deleted.')
        except Exception as e:
            db.session.rollback()
            flash(f'An unexpected error occurred: {str(e)}')
    else:
        flash('Customer not found!')
    return redirect(url_for('view_customers'))

# --- Sales Management ---

@app.route('/sales')
def view_sales():
    sales = Sale.query.all()
    return render_template('view_sales.html', sales=sales)

@app.route('/sales/add', methods=['GET', 'POST'])
def add_sale():
    if request.method == 'POST':
        vin = request.form['vin']
        customer_id = request.form['customer_id']
        price_sold = request.form['price_sold']
        payment_method = request.form['payment_method']
        warranty_period = request.form['warranty_period']
        purchase_date = request.form['purchase_date']
        new_sale = Sale(
            vin=vin,
            customer_id=customer_id,
            price_sold=price_sold,
            payment_method=payment_method,
            warranty_period=warranty_period,
            purchase_date=date.fromisoformat(purchase_date)
        )
        db.session.add(new_sale)
        db.session.commit()
        flash('Sale added successfully!')
        return redirect(url_for('view_sales'))
    return render_template('add_sale.html')

@app.route('/sales/edit/<vin>/<customer_id>', methods=['GET', 'POST'])
def edit_sale(vin, customer_id):
    sale = Sale.query.filter_by(vin=vin, customer_id=customer_id).first()
    if request.method == 'POST':
        sale.price_sold = request.form['price_sold']
        sale.payment_method = request.form['payment_method']
        sale.warranty_period = request.form['warranty_period']
        sale.purchase_date = date.fromisoformat(request.form['purchase_date'])
        db.session.commit()
        flash('Sale updated successfully!')
        return redirect(url_for('view_sales'))
    return render_template('edit_sale.html', sale=sale)

@app.route('/sales/delete/<vin>/<customer_id>')
def delete_sale(vin, customer_id):
    sale = Sale.query.filter_by(vin=vin, customer_id=customer_id).first()
    db.session.delete(sale)
    db.session.commit()
    flash('Sale deleted successfully!')
    return redirect(url_for('view_sales'))

# --- Employee Management ---

@app.route('/employees', methods=['GET', 'POST'])
def manage_employees():
    if 'role' in session and session['role'] == 'Admin':
        if request.method == 'POST':
            dealer_id = request.form['dealer_id']
            name = request.form['name']
            position = request.form['position']
            salary = request.form['salary']
            contact = request.form['contact']
            supervisor_id = request.form['supervisor_id'] or None
            new_employee = Employee(
                dealer_id=dealer_id, name=name, position=position,
                salary=salary, contact=contact, supervisor_id=supervisor_id
            )
            db.session.add(new_employee)
            db.session.commit()
            flash('Employee added successfully!')
            return redirect(url_for('manage_employees'))
        employees = Employee.query.all()
        dealers = Dealer.query.all()
        return render_template('manage_employees.html', employees=employees, dealers=dealers)
    return redirect(url_for('index'))

@app.route('/edit_employee/<int:employee_id>', methods=['GET', 'POST'])
def edit_employee(employee_id):
    if 'role' in session and session['role'] == 'Admin':
        employee = db.session.get(Employee, employee_id)
        dealers = Dealer.query.all()
        employees = Employee.query.all()
        if request.method == 'POST':
            employee.dealer_id = request.form['dealer_id']
            employee.name = request.form['name']
            employee.position = request.form['position']
            employee.salary = request.form['salary']
            employee.contact = request.form['contact']
            employee.supervisor_id = request.form['supervisor_id'] or None
            db.session.commit()
            flash('Employee details updated successfully!')
            return redirect(url_for('manage_employees'))
        return render_template('edit_employee.html', employee=employee, dealers=dealers, employees=employees)
    return redirect(url_for('index'))

@app.route('/delete_employee/<int:employee_id>', methods=['POST'])
def delete_employee(employee_id):
    if 'role' in session and session['role'] == 'Admin':
        employee = db.session.get(Employee, employee_id)
        db.session.delete(employee)
        db.session.commit()
        flash('Employee deleted successfully!')
        return redirect(url_for('manage_employees'))
    return redirect(url_for('index'))

# --- Service Management ---

@app.route('/services', methods=['GET'])
def view_services():
    services = Service.query.all()
    return render_template('view_services.html', services=services)

@app.route('/add_service', methods=['GET', 'POST'])
def add_service():
    if request.method == 'POST':
        vin = request.form.get('vin')
        customer_id = request.form.get('customer_id')
        service_id = request.form.get('service_id')
        service_date = request.form.get('service_date')
        service_detail = request.form.get('service_detail')
        if not all([vin, customer_id, service_id, service_date, service_detail]):
            flash("Error: Service not added. Please ensure all fields are correct.")
            return redirect(url_for('add_service'))
        new_service = Service(
            vin=vin, customer_id=customer_id, service_id=service_id,
            service_date=date.fromisoformat(service_date), service_detail=service_detail
        )
        try:
            db.session.add(new_service)
            db.session.commit()
            flash("Service added successfully!")
            return redirect(url_for('view_services'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}")
    return render_template('add_service.html')

@app.route('/edit_service/<string:vin>/<int:customer_id>/<int:service_id>', methods=['GET', 'POST'])
def edit_service(vin, customer_id, service_id):
    service = db.session.get(Service, (vin, customer_id, service_id))
    if service is None:
        flash("Service not found")
        return redirect(url_for('view_services'))
    if request.method == 'POST':
        service.service_date = date.fromisoformat(request.form['service_date'])
        service.service_detail = request.form['service_detail']
        db.session.commit()
        flash("Service updated successfully!")
        return redirect(url_for('view_services'))
    return render_template('edit_service.html', service=service)

@app.route('/delete_service/<vin>/<int:customer_id>/<int:service_id>', methods=['POST'])
def delete_service(vin, customer_id, service_id):
    service = Service.query.filter_by(vin=vin, customer_id=customer_id, service_id=service_id).first()
    if service:
        try:
            db.session.delete(service)
            db.session.commit()
            flash("Service deleted successfully!")
        except Exception as e:
            db.session.rollback()
            flash(f"Error: Could not delete service. {str(e)}")
    else:
        flash("Service not found.")
    return redirect(url_for('view_services'))

# --- Inventory Management ---

@app.route('/inventory/<int:dealer_id>', methods=['GET'])
def view_inventory(dealer_id):
    inventory = Inventory.query.filter_by(dealer_id=dealer_id).all()
    return render_template('view_inventory.html', inventory=inventory, dealer_id=dealer_id)

@app.route('/inventory/edit/<int:dealer_id>/<string:vin>', methods=['GET', 'POST'])
def edit_inventory(dealer_id, vin):
    inventory_item = Inventory.query.filter_by(dealer_id=dealer_id, vin=vin).first_or_404()
    if request.method == 'POST':
        try:
            inventory_item.stock_quantity = int(request.form['stock_quantity'])
            inventory_item.price_offered = float(request.form['price_offered'])
            db.session.commit()
            return redirect(url_for('view_inventory', dealer_id=dealer_id))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating inventory: {str(e)}")
    return render_template('edit_inventory.html', inventory_item=inventory_item)

# --- Customer-Facing Views ---

@app.route('/customer/inventory', methods=['GET'])
def customer_view_inventory():
    inventory = db.session.query(Inventory, Vehicle).join(Vehicle, Vehicle.vin == Inventory.vin).all()
    return render_template('customer_inventory.html', inventory=inventory)

@app.route('/purchase_history', methods=['GET', 'POST'])
def view_purchase_history():
    if request.method == 'POST':
        customer_id = request.form['customer_id']
        purchases = Sale.query.filter_by(customer_id=customer_id).all()
        for purchase in purchases:
            purchase.vehicle = Vehicle.query.filter_by(vin=purchase.vin).first()
        return render_template('view_purchase_history.html', purchases=purchases)
    return render_template('purchase_history_form.html')

@app.route('/service_history', methods=['GET', 'POST'])
def view_service_history():
    if request.method == 'POST':
        customer_id = request.form['customer_id']
        services = Service.query.filter_by(customer_id=customer_id).all()
        for service in services:
            service.vehicle = Vehicle.query.filter_by(vin=service.vin).first()
        return render_template('view_service_history.html', services=services)
    return render_template('service_history_form.html')

# Note: The if __name__ == '__main__': block is intentionally omitted
# because a production server like Gunicorn will run the 'app' object directly.

