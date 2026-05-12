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
    from app.ceo import ceo_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp, url_prefix='')
    app.register_blueprint(sales_bp, url_prefix='/sales')
    app.register_blueprint(services_bp, url_prefix='/services')
    app.register_blueprint(expenses_bp, url_prefix='/expenses')
    app.register_blueprint(barbers_bp, url_prefix='/barbers')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(ceo_bp)
    
    # Create tables and add sample data
    with app.app_context():
        db.create_all()
        
        # === MIGRATION: Add role column to admins ===
        try:
            import sqlite3
            db_uri = app.config['SQLALCHEMY_DATABASE_URI']
            if db_uri and db_uri.startswith('sqlite:///'):
                db_path = db_uri.replace('sqlite:///', '')
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(admins)")
                columns = [row[1] for row in cursor.fetchall()]
                if 'role' not in columns:
                    cursor.execute("ALTER TABLE admins ADD COLUMN role VARCHAR(20) DEFAULT 'admin'")
                    conn.commit()
                    print("✅ Added role column to admins table")
                else:
                    print("✓ role column already exists")
                conn.close()
        except Exception as e:
            print(f"⚠️ Migration check failed: {e}")
        
        # === MIGRATION: Add settled_amount column to barber_advances ===
        try:
            import sqlite3
            db_uri = app.config['SQLALCHEMY_DATABASE_URI']
            if db_uri and db_uri.startswith('sqlite:///'):
                db_path = db_uri.replace('sqlite:///', '')
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(barber_advances)")
                columns = [row[1] for row in cursor.fetchall()]
                if 'settled_amount' not in columns:
                    cursor.execute("ALTER TABLE barber_advances ADD COLUMN settled_amount FLOAT DEFAULT 0.00")
                    conn.commit()
                    print("✅ Added settled_amount column to barber_advances")
                else:
                    print("✓ settled_amount column already exists")
                conn.close()
        except Exception as e:
            print(f"⚠️ Migration check failed: {e}")

        # === MIGRATION: Add password_hash column to barbers ===
        try:
            import sqlite3
            db_uri = app.config['SQLALCHEMY_DATABASE_URI']
            if db_uri and db_uri.startswith('sqlite:///'):
                db_path = db_uri.replace('sqlite:///', '')
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(barbers)")
                columns = [row[1] for row in cursor.fetchall()]
                if 'password_hash' not in columns:
                    cursor.execute("ALTER TABLE barbers ADD COLUMN password_hash VARCHAR(200)")
                    conn.commit()
                    print("✅ Added password_hash column to barbers table")
                else:
                    print("✓ password_hash column already exists")
                conn.close()
        except Exception as e:
            print(f"⚠️ Migration check failed: {e}")
        
        # === MIGRATION: Add status and original_amount to sales table ===
        try:
            import sqlite3
            db_uri = app.config['SQLALCHEMY_DATABASE_URI']
            if db_uri and db_uri.startswith('sqlite:///'):
                db_path = db_uri.replace('sqlite:///', '')
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(sales)")
                columns = [row[1] for row in cursor.fetchall()]
                if 'status' not in columns:
                    cursor.execute("ALTER TABLE sales ADD COLUMN status VARCHAR(20) DEFAULT 'active'")
                    print("✅ Added status column to sales table")
                if 'original_amount' not in columns:
                    cursor.execute("ALTER TABLE sales ADD COLUMN original_amount FLOAT")
                    print("✅ Added original_amount column to sales table")
                conn.commit()
                conn.close()
        except Exception as e:
            print(f"⚠️ Migration check failed: {e}")

        # Update/Create admin and CEO with environment variables
        admin_username = Config.ADMIN_USERNAME
        admin_password = Config.ADMIN_PASSWORD
        
        ceo_username = Config.CEO_USERNAME
        ceo_password = Config.CEO_PASSWORD
        
        # Update or create Admin
        admin = Admin.query.filter_by(username=admin_username).first()
        if admin:
            admin.set_password(admin_password)
            print(f"✓ Admin password updated")
        else:
            admin = Admin(username=admin_username, role='admin')
            admin.set_password(admin_password)
            db.session.add(admin)
            print(f"✓ Admin created")
        
        # Update or create CEO
        ceo = Admin.query.filter_by(username=ceo_username).first()
        if ceo:
            ceo.set_password(ceo_password)
            print(f"✓ CEO password updated")
        else:
            ceo = Admin(username=ceo_username, role='ceo')
            ceo.set_password(ceo_password)
            db.session.add(ceo)
            print(f"✓ CEO created")
        
        db.session.commit()
        
        # Create sample barbers and services only if empty (preserve existing data)
        if Barber.query.count() == 0:
            barbers = [
                Barber(name='James Wilson', phone='+1234567890', email='james@barbershop.com'),
                Barber(name='Michael Brown', phone='+1234567891', email='michael@barbershop.com'),
                Barber(name='David Lee', phone='+1234567892', email='david@barbershop.com')
            ]
            for barber in barbers:
                db.session.add(barber)
            db.session.commit()
            print("✓ Sample barbers created")
        
        if Service.query.count() == 0:
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
            print("✓ Sample services created")
        
        # Add sample sales only if none exist
        if Sale.query.count() == 0:
            barbers = Barber.query.all()
            services = Service.query.all()
            if barbers and services:
                today = date.today()
                for i in range(5):
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
        
        if Expense.query.count() == 0:
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
        
        if BarberAdvance.query.count() == 0:
            barbers = Barber.query.all()
            if barbers:
                advance = BarberAdvance(
                    barber_id=barbers[0].id,
                    amount=50.00,
                    advance_date=today - timedelta(days=2),
                    note='Personal advance'
                )
                db.session.add(advance)
                db.session.commit()
                print("✓ Sample advance created")
        
        print(f"\n✅ Database ready!")
        print(f"   Admin: {Config.ADMIN_USERNAME} / {Config.ADMIN_PASSWORD}")
        print(f"   CEO: {Config.CEO_USERNAME} / {Config.CEO_PASSWORD}")
    
    return app

# Blueprint initialization files
from app.auth import auth_bp
from app.main import main_bp
from app.sales import sales_bp
from app.services import services_bp
from app.expenses import expenses_bp
from app.barbers import barbers_bp
from app.reports import reports_bp
from app.ceo import ceo_bp