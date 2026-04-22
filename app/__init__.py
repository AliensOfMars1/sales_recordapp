from flask import Flask
from config import Config
from app.extensions import db, login_manager, init_login_manager
from app.models import Admin, Barber, Service, Sale, Expense, BarberAdvance
from datetime import datetime, date, timedelta

def create_app(config_class=Config):
    app = Flask(__name__, instance_path=None)
    app.config.from_object(config_class)
    
    # Ensure instance folder exists
    import os
    if not os.path.exists(app.instance_path):
        os.makedirs(app.instance_path)
    
    # Initialize extensions
    db.init_app(app)
    
    # Initialize login manager with user loader
    init_login_manager(app)
    
    # Register blueprints
    from app.auth import auth_bp
    from app.main import main_bp
    from app.sales import sales_bp
    from app.services import services_bp
    from app.expenses import expenses_bp
    from app.barbers import barbers_bp
    from app.reports import reports_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp, url_prefix='')
    app.register_blueprint(sales_bp, url_prefix='/sales')
    app.register_blueprint(services_bp, url_prefix='/services')
    app.register_blueprint(expenses_bp, url_prefix='/expenses')
    app.register_blueprint(barbers_bp, url_prefix='/barbers')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    
    # Create tables and add sample data
    with app.app_context():
        db.create_all()
        
        # Add sample data if database is empty
        if Admin.query.count() == 0:
            print("Creating sample data...")
            
            # Create admin
            admin = Admin(username='admin')
            admin.set_password('barber2024')
            db.session.add(admin)
            db.session.commit()
            print("✓ Admin created")
            
            # Sample barbers
            barbers = [
                Barber(name='James Wilson', phone='+1234567890', email='james@barbershop.com'),
                Barber(name='Michael Brown', phone='+1234567891', email='michael@barbershop.com'),
                Barber(name='David Lee', phone='+1234567892', email='david@barbershop.com')
            ]
            for barber in barbers:
                db.session.add(barber)
            db.session.commit()
            print("✓ Barbers created")
            
            # Sample services
            services = [
                Service(name='Haircut', default_price=30.00, description='Classic haircut'),
                Service(name='Beard Trim', default_price=15.00, description='Professional beard grooming'),
                Service(name='Haircut + Beard', default_price=40.00, description='Complete grooming package'),
                Service(name='Hot Towel Shave', default_price=25.00, description='Traditional hot towel shave'),
                Service(name='Kids Haircut', default_price=20.00, description='For children under 12')
            ]
            for service in services:
                db.session.add(service)
            db.session.commit()
            print("✓ Services created")
            
            # Add sample sales
            today = date.today()
            for i in range(5):  # Add 5 sample sales
                sale = Sale(
                    barber_id=barbers[i % 3].id,
                    service_id=services[i % 5].id,
                    amount=services[i % 5].default_price,
                    payment_method='cash' if i % 2 == 0 else 'momo',
                    sale_date=today - timedelta(days=i),
                    notes=f'Sample sale {i+1}'
                )
                db.session.add(sale)
            db.session.commit()
            print("✓ Sample sales created")
            
            # Add sample expense
            expense = Expense(
                title='Monthly Rent',
                amount=2000.00,
                category='rent',
                expense_date=today,
                notes='Shop rent for the month'
            )
            db.session.add(expense)
            db.session.commit()
            print("✓ Sample expense created")
            
            # Add sample advance (now barbers exist)
            advance = BarberAdvance(
                barber_id=barbers[0].id,  # James Wilson
                amount=50.00,
                advance_date=today - timedelta(days=2),
                note='Personal advance'
            )
            db.session.add(advance)
            db.session.commit()
            print("✓ Sample advance created")
            
            print("\n✅ Database initialized successfully with sample data!")
            print(f"   Admin credentials: admin / barber2024")
            print(f"   Sample barbers: {len(barbers)}")
            print(f"   Sample services: {len(services)}")
    
    return app

# Blueprint initialization files (create these as separate files)
from app.auth import auth_bp
from app.main import main_bp
from app.sales import sales_bp
from app.services import services_bp
from app.expenses import expenses_bp
from app.barbers import barbers_bp
from app.reports import reports_bp