from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db

class Admin(UserMixin, db.Model):
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        return str(self.id)

class Barber(db.Model):
    __tablename__ = 'barbers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sales = db.relationship('Sale', backref='barber', lazy=True, cascade='all, delete-orphan')
    advances = db.relationship('BarberAdvance', backref='barber', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Barber {self.name}>'
    
    def total_sales(self, start_date=None, end_date=None):
        query = Sale.query.filter_by(barber_id=self.id)
        if start_date:
            query = query.filter(Sale.sale_date >= start_date)
        if end_date:
            query = query.filter(Sale.sale_date <= end_date)
        return sum([sale.amount for sale in query.all()]) or 0
    
    def total_advances(self, start_date=None, end_date=None):
        """Get total outstanding advance amount for a barber in a date range"""
        query = BarberAdvance.query.filter(
            BarberAdvance.barber_id == self.id,
            BarberAdvance.settled == False
        )
        
        if start_date:
            query = query.filter(BarberAdvance.advance_date >= start_date)
        if end_date:
            query = query.filter(BarberAdvance.advance_date <= end_date)
        
        advances = query.all()
        
        # Sum remaining balances (original amount - settled amount)
        total = sum(a.remaining_balance for a in advances)
        return total or 0

class Service(db.Model):
    __tablename__ = 'services'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    default_price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sales = db.relationship('Sale', backref='service', lazy=True)
    
    def __repr__(self):
        return f'<Service {self.name} - ${self.default_price}>'

class Sale(db.Model):
    __tablename__ = 'sales'
    
    id = db.Column(db.Integer, primary_key=True)
    barber_id = db.Column(db.Integer, db.ForeignKey('barbers.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    custom_service_name = db.Column(db.String(100))
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)  # 'cash' or 'momo'
    sale_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Sale {self.id} - ${self.amount}>'

class Expense(db.Model):
    __tablename__ = 'expenses'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    expense_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Expense {self.title} - ${self.amount}>'

class BarberAdvance(db.Model):
    __tablename__ = 'barber_advances'
    
    id = db.Column(db.Integer, primary_key=True)
    barber_id = db.Column(db.Integer, db.ForeignKey('barbers.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    settled_amount = db.Column(db.Float, default=0.00)  # NEW: tracks how much has been repaid
    advance_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    note = db.Column(db.Text)
    settled = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def remaining_balance(self):
        """Calculate how much is still owed"""
        return self.amount - (self.settled_amount or 0)
    
    def __repr__(self):
        return f'<Advance {self.amount} for Barber {self.barber_id}>'