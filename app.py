from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import Vehicle, Brand, Model, db,Dealer,Service,Inventory,Sale
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User,Customer,Sale,Employee
from datetime import date
from sqlalchemy.exc import IntegrityError


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:new_password@localhost/automobileDBMS'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'

db.init_app(app)
migrate = Migrate(app, db)

@app.route('/')
def index():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username).first()

    if user and user.password == password:  # For plain-text passwords
        session['user_id'] = user.id
        session['role'] = user.role

        if user.role == 'Admin':
            return redirect(url_for('admin_dashboard'))
        elif user.role == 'Dealer':
            # Pass the user ID directly to the dealer dashboard
            return redirect(url_for('dealer_dashboard', dealer_id=user.id))
        elif user.role == 'Customer':
            return redirect(url_for('customer_dashboard'))

    flash('Invalid credentials!')
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form.get('role', 'Customer')  # Default role is Customer

        if User.query.filter_by(username=username).first():
            flash('Username already exists!')
            return redirect(url_for('register'))

        
        new_user = User(username=username, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully! Please login.')
        return redirect(url_for('index'))

    return render_template('register.html')

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
@app.route('/vehicles', methods=['GET', 'POST'])
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
                new_vehicle = Vehicle(
                    vin=vin, brand_id=brand_id, model_id=model_id,
                    price=price, color=color, year=year
                )
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
        vehicle = Vehicle.query.get(vin)
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
            vehicle = Vehicle.query.get(vin)
            db.session.delete(vehicle)
            db.session.commit()
            flash('Vehicle deleted successfully!')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}')
    return redirect(url_for('manage_vehicles'))




@app.route('/dealers')
def view_dealers():
    """Route to view all dealers."""
    dealers = Dealer.query.all()  # Fetch all dealers
    return render_template('view_dealers.html', dealers=dealers)

@app.route('/dealers/add', methods=['GET', 'POST'])
def add_dealer():
    """Route to add a new dealer."""
    if request.method == 'POST':
        id = request.form['id']
        name = request.form['name']
        contact = request.form['contact']
        new_dealer = Dealer(id = id,name=name, contact=contact)
        db.session.add(new_dealer)
        db.session.commit()
        flash('Dealer added successfully!')
        return redirect(url_for('view_dealers'))
    return render_template('add_dealer.html')

@app.route('/dealers/edit/<int:id>', methods=['GET', 'POST'])
def edit_dealer(id):
    """Route to edit an existing dealer."""
    dealer = Dealer.query.get(id)
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
    """Route to delete a dealer."""
    dealer = Dealer.query.get(id)
    if dealer:
        db.session.delete(dealer)
        db.session.commit()
        flash('Dealer deleted successfully!')
    else:
        flash('Dealer not found!')
    return redirect(url_for('view_dealers'))


@app.route('/customers')
def view_customers():
    """Route to view all customers."""
    customers = Customer.query.all()  # Fetch all customers
    return render_template('view_customers.html', customers=customers)

@app.route('/customers/add', methods=['GET', 'POST'])
def add_customer():
    """Route to add a new customer."""
    if request.method == 'POST':
        customer_id = request.form['customer_id'] 
        name = request.form['name']
        street = request.form['street']
        city = request.form['city']
        state = request.form['state']
        zip_code = request.form['zip_code']
        
        new_customer = Customer(id=customer_id,name=name, street=street, city=city, state=state, zip_code=zip_code)
        db.session.add(new_customer)
        db.session.commit()
        flash('Customer added successfully!')
        return redirect(url_for('view_customers'))
    
    return render_template('add_customer.html')

@app.route('/customers/edit/<int:id>', methods=['GET', 'POST'])
def edit_customer(id):
    """Route to edit an existing customer."""
    customer = Customer.query.get(id)
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
    """Route to delete a customer."""
    customer = Customer.query.get(id)
    if customer:
        db.session.delete(customer)
        db.session.commit()
        flash('Customer deleted successfully!')
    else:
        flash('Customer not found!')
    return redirect(url_for('view_customers'))



@app.route('/sales')
def view_sales():
    """Route to view all sales."""
    sales = Sale.query.all()  # Get all sales
    return render_template('view_sales.html', sales=sales)

@app.route('/sales/add', methods=['GET', 'POST'])
def add_sale():
    """Route to add a new sale."""
    if request.method == 'POST':
        vin = request.form['vin']  # Vehicle VIN
        customer_id = request.form['customer_id']  # Customer ID
        price_sold = request.form['price_sold']
        payment_method = request.form['payment_method']
        warranty_period = request.form['warranty_period']
        purchase_date = request.form['purchase_date']

        # Create a new Sale record
        new_sale = Sale(
            vin=vin,
            customer_id=customer_id,
            price_sold=price_sold,
            payment_method=payment_method,
            warranty_period=warranty_period,
            purchase_date=date.fromisoformat(purchase_date)  # Convert string to date
        )

        db.session.add(new_sale)
        db.session.commit()
        flash('Sale added successfully!')
        return redirect(url_for('view_sales'))

    return render_template('add_sale.html')

@app.route('/sales/edit/<vin>/<customer_id>', methods=['GET', 'POST'])
def edit_sale(vin, customer_id):
    """Route to edit an existing sale."""
    sale = Sale.query.filter_by(vin=vin, customer_id=customer_id).first()  # Find sale by VIN and Customer ID
    if request.method == 'POST':
        sale.price_sold = request.form['price_sold']
        sale.payment_method = request.form['payment_method']
        sale.warranty_period = request.form['warranty_period']
        sale.purchase_date = request.form['purchase_date']

        db.session.commit()
        flash('Sale updated successfully!')
        return redirect(url_for('view_sales'))

    return render_template('edit_sale.html', sale=sale)

@app.route('/sales/delete/<vin>/<customer_id>')
def delete_sale(vin, customer_id):
    """Route to delete a sale."""
    sale = Sale.query.filter_by(vin=vin, customer_id=customer_id).first()
    db.session.delete(sale)
    db.session.commit()
    flash('Sale deleted successfully!')
    return redirect(url_for('view_sales'))

@app.route('/employees', methods=['GET', 'POST'])
def manage_employees():
    if 'role' in session and session['role'] == 'Admin':
        if request.method == 'POST':
            # Adding a new employee
            dealer_id = request.form['dealer_id']
            name = request.form['name']
            position = request.form['position']
            salary = request.form['salary']
            contact = request.form['contact']
            supervisor_id = request.form['supervisor_id'] or None  # Optional supervisor
            
            # Add to the database
            new_employee = Employee(
                dealer_id=dealer_id,
                name=name,
                position=position,
                salary=salary,
                contact=contact,
                supervisor_id=supervisor_id
            )
            db.session.add(new_employee)
            db.session.commit()

            flash('Employee added successfully!')
            return redirect(url_for('manage_employees'))

        # GET method: View all employees
        employees = Employee.query.all()
        dealers = Dealer.query.all()  # Get all dealers for the dropdown in the form
        return render_template('manage_employees.html', employees=employees, dealers=dealers)
    return redirect(url_for('index'))
@app.route('/edit_employee/<int:employee_id>', methods=['GET', 'POST'])
def edit_employee(employee_id):
    if 'role' in session and session['role'] == 'Admin':
        employee = Employee.query.get_or_404(employee_id)
        dealers = Dealer.query.all()
        employees = Employee.query.all()

        if request.method == 'POST':
            # Update employee details
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
        employee = Employee.query.get_or_404(employee_id)
        db.session.delete(employee)
        db.session.commit()
        flash('Employee deleted successfully!')
        return redirect(url_for('manage_employees'))
    return redirect(url_for('index'))


@app.route('/services', methods=['GET'])
def view_services():
    services = Service.query.all()  # Retrieve all services from the database
    return render_template('view_services.html', services=services)
@app.route('/add_service', methods=['GET', 'POST'])
def add_service():
    if request.method == 'POST':
        vin = request.form.get('vin')
        customer_id = request.form.get('customer_id')
        service_id = request.form.get('service_id')  # Get service_id from form
        service_date = request.form.get('service_date')
        service_detail = request.form.get('service_detail')

        # Ensure all fields are present
        if not vin or not customer_id or not service_id or not service_date or not service_detail:
            return "Error: Service not added. Please ensure all fields are correct."

        # Create a new service object
        new_service = Service(
            vin=vin,
            customer_id=customer_id,
            service_id=service_id,  # Set service_id from the form
            service_date=service_date,
            service_detail=service_detail
        )

        try:
            # Add the service to the database
            db.session.add(new_service)
            db.session.commit()
            return redirect(url_for('view_services'))  # Redirect to view services page
        except Exception as e:
            db.session.rollback()
            return f"Error: {str(e)}"

    return render_template('add_service.html')  # Render the form for adding a new service





@app.route('/edit_service/<string:vin>/<int:customer_id>/<int:service_id>', methods=['GET', 'POST'])
def edit_service(vin, customer_id, service_id):
    # Retrieve the service using the composite primary key (vin, customer_id, service_id)
    service = Service.query.get((vin, customer_id, service_id))
    
    if service is None:
        return "Service not found", 404  # Handle case where service is not found
    
    if request.method == 'POST':
        # Update the service details with the form data
        service.service_date = request.form['service_date']
        service.service_detail = request.form['service_detail']
        db.session.commit()
        return redirect(url_for('view_services'))  # Redirect to services list after update
    
    return render_template('edit_service.html', service=service)



@app.route('/delete_service/<vin>/<int:customer_id>/<int:service_id>', methods=['GET'])
def delete_service(vin, customer_id, service_id):
    # Retrieve the service record to be deleted
    service = Service.query.filter_by(vin=vin, customer_id=customer_id, service_id=service_id).first()
    
    if service:
        try:
            db.session.delete(service)
            db.session.commit()
            return redirect(url_for('view_services'))  # Redirect to the services list after deletion
        except Exception as e:
            db.session.rollback()
            return f"Error: Could not delete service. {str(e)}"
    else:
        return "Service not found."
@app.route('/inventory/<int:dealer_id>', methods=['GET'])
def view_inventory(dealer_id):
    """Displays the inventory for a specific dealer."""
    inventory = Inventory.query.filter_by(dealer_id=dealer_id).all()
    return render_template('view_inventory.html', inventory=inventory, dealer_id=dealer_id)


@app.route('/inventory/edit/<int:dealer_id>/<string:vin>', methods=['GET', 'POST'])
def edit_inventory(dealer_id, vin):
    """Edits a specific inventory item."""
    inventory_item = Inventory.query.filter_by(dealer_id=dealer_id, vin=vin).first()
    if not inventory_item:
        return "Inventory item not found", 404

    if request.method == 'POST':
        try:
            inventory_item.stock_quantity = int(request.form['stock_quantity'])
            inventory_item.price_offered = float(request.form['price_offered'])
            db.session.commit()
            return redirect(url_for('view_inventory', dealer_id=dealer_id))
        except Exception as e:
            db.session.rollback()
            return f"Error updating inventory: {str(e)}"

    return render_template('edit_inventory.html', inventory_item=inventory_item)

@app.route('/customer/inventory', methods=['GET'])
def customer_view_inventory():
    """Displays all vehicles available in the inventory for customers."""
    # Query the Inventory table and join with the Vehicle table to get details
    inventory = db.session.query(Inventory, Vehicle).join(Vehicle, Vehicle.vin == Inventory.vin).all()

    return render_template('customer_inventory.html', inventory=inventory)


@app.route('/purchase_history', methods=['GET', 'POST'])
def view_purchase_history():
    if request.method == 'POST':
        customer_id = request.form['customer_id']
        purchases = db.session.query(Sale).filter_by(customer_id=customer_id).all()

        # Add logic to include vehicle details based on the 'vin' foreign key
        for purchase in purchases:
            purchase.vehicle = Vehicle.query.filter_by(vin=purchase.vin).first()  # Assuming 'vin' is in Sale table
        
        return render_template('view_purchase_history.html', purchases=purchases)

    return render_template('purchase_history_form.html')
@app.route('/service_history', methods=['GET', 'POST'])
def view_service_history():
    if request.method == 'POST':
        customer_id = request.form['customer_id']
        
        # Query the service history based on customer_id
        services = db.session.query(Service).filter_by(customer_id=customer_id).all()

        # Include additional details about the service (if needed)
        for service in services:
            service.vehicle = Vehicle.query.filter_by(vin=service.vin).first()  # Assuming 'vin' is in the Service table
        
        return render_template('view_service_history.html', services=services)

    return render_template('service_history_form.html')













if __name__ == '__main__':
    app.run(debug=True)
