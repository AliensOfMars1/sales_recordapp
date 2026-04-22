from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SelectField, DateField, TextAreaField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, ValidationError
from datetime import datetime

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

class SaleForm(FlaskForm):
    barber_id = SelectField('Barber', coerce=int, validators=[DataRequired()])
    service_id = SelectField('Service', coerce=int, validators=[DataRequired()])
    amount = FloatField('Sale Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    payment_method = SelectField('Payment Method', choices=[('cash', 'Cash'), ('momo', 'Mobile Money (MoMo)')], validators=[DataRequired()])
    sale_date = DateField('Sale Date', validators=[DataRequired()], default=datetime.today)
    notes = TextAreaField('Notes', validators=[Optional()])
    
    def __init__(self, *args, **kwargs):
        super(SaleForm, self).__init__(*args, **kwargs)
        from app.models import Barber, Service
        self.barber_id.choices = [(b.id, b.name) for b in Barber.query.filter_by(active=True).order_by('name').all()]
        self.service_id.choices = [(s.id, f"{s.name} - ${s.default_price}") for s in Service.query.filter_by(active=True).order_by('name').all()]

class ExpenseForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    category = SelectField('Category', choices=[
        ('rent', 'Rent'), ('utilities', 'Utilities'), ('supplies', 'Supplies'),
        ('marketing', 'Marketing'), ('maintenance', 'Maintenance'), ('other', 'Other')
    ], validators=[DataRequired()])
    expense_date = DateField('Expense Date', validators=[DataRequired()], default=datetime.today)
    notes = TextAreaField('Notes', validators=[Optional()])

class ServiceForm(FlaskForm):
    name = StringField('Service Name', validators=[DataRequired(), Length(max=100)])
    default_price = FloatField('Default Price', validators=[DataRequired(), NumberRange(min=0.01)])
    description = TextAreaField('Description', validators=[Optional()])
    active = BooleanField('Active', default=True)

class BarberForm(FlaskForm):
    name = StringField('Barber Name', validators=[DataRequired(), Length(max=100)])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    email = StringField('Email', validators=[Optional(), Length(max=100)])
    active = BooleanField('Active', default=True)

class BorrowForm(FlaskForm):
    barber_id = SelectField('Barber', coerce=int, validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    advance_date = DateField('Date', validators=[DataRequired()], default=datetime.today)
    note = TextAreaField('Reason/Note', validators=[Optional()])
    
    def __init__(self, *args, **kwargs):
        super(BorrowForm, self).__init__(*args, **kwargs)
        from app.models import Barber
        self.barber_id.choices = [(b.id, b.name) for b in Barber.query.filter_by(active=True).order_by('name').all()]