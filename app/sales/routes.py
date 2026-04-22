from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required
from app.extensions import db
from app.sales import sales_bp
from app.forms import SaleForm
from app.models import Sale, Service, Barber
from datetime import datetime, date

@sales_bp.route('/record', methods=['GET', 'POST'])
@login_required
def record_sale():
    form = SaleForm()
    
    if form.validate_on_submit():
        sale = Sale(
            barber_id=form.barber_id.data,
            service_id=form.service_id.data,
            amount=form.amount.data,
            payment_method=form.payment_method.data,
            sale_date=form.sale_date.data,
            notes=form.notes.data
        )
        db.session.add(sale)
        db.session.commit()
        flash('Sale recorded successfully!', 'success')
        return redirect(url_for('sales.record_sale'))
    
    # For multiple barber forms (horizontal scroll)
    barbers = Barber.query.filter_by(active=True).order_by(Barber.name).all()
    services = Service.query.filter_by(active=True).order_by(Service.name).all()
    today_date = date.today().isoformat()
    
    return render_template('sales/record_sale.html',
                         form=form,
                         barbers=barbers,
                         services=services,
                         today_date=today_date)

@sales_bp.route('/get-service-price/<int:service_id>')
@login_required
def get_service_price(service_id):
    service = Service.query.get_or_404(service_id)
    return jsonify({'price': service.default_price})

@sales_bp.route('/list')
@login_required
def list_sales():
    """View all sales with edit/delete options"""
    sales = Sale.query.order_by(Sale.sale_date.desc(), Sale.created_at.desc()).all()
    return render_template('sales/list_sales.html', sales=sales)

@sales_bp.route('/edit/<int:sale_id>', methods=['GET', 'POST'])
@login_required
def edit_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    
    if request.method == 'POST':
        sale.barber_id = int(request.form.get('barber_id'))
        sale.service_id = int(request.form.get('service_id'))
        sale.amount = float(request.form.get('amount'))
        sale.payment_method = request.form.get('payment_method')
        sale.sale_date = datetime.strptime(request.form.get('sale_date'), '%Y-%m-%d').date()
        sale.notes = request.form.get('notes')
        
        db.session.commit()
        flash('Sale updated successfully!', 'success')
        return redirect(url_for('sales.list_sales'))
    
    barbers = Barber.query.filter_by(active=True).all()
    services = Service.query.filter_by(active=True).all()
    return render_template('sales/edit_sale.html', sale=sale, barbers=barbers, services=services)

@sales_bp.route('/delete/<int:sale_id>')
@login_required
def delete_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    db.session.delete(sale)
    db.session.commit()
    flash('Sale deleted successfully!', 'success')
    return redirect(url_for('sales.list_sales'))