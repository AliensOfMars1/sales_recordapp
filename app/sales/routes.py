from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required
from app.extensions import db
from app.sales import sales_bp
from app.forms import SaleForm
from app.models import Sale, Service, Barber
from datetime import datetime, date, timedelta
 

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
    # Debug print
    print("=== LIST SALES ROUTE CALLED ===")
    
    # Get selected date from query string (default to today)
    date_str = request.args.get('date')
    print(f"Date from URL: {date_str}")
    
    if date_str:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        selected_date = datetime.now().date()
    
    print(f"Selected date: {selected_date}")
    
    # Calculate current week (Monday to Sunday) for dropdown options
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())
    
    # Get week days for dropdown (Monday to Sunday of current week)
    week_days = []
    for i in range(7):
        day_date = week_start + timedelta(days=i)
        week_days.append({
            'name': day_date.strftime('%A'),
            'date': day_date.strftime('%Y-%m-%d')
        })
    
    print(f"Week days generated: {week_days}")  # Should show 7 days
    
    # Get all active barbers
    barbers = Barber.query.filter_by(active=True).all()
    print(f"Active barbers count: {len(barbers)}")
    
    # Build data for each barber
    sales_by_barber = []
    for barber in barbers:
        day_sales = Sale.query.filter(
            Sale.barber_id == barber.id,
            Sale.sale_date == selected_date,
            Sale.status != 'deleted'
        ).order_by(Sale.created_at.desc()).all()
        
        print(f"Barber {barber.name}: {len(day_sales)} sales on {selected_date}")
        
        if day_sales:
            sales_by_barber.append({
                'barber': barber,
                'sales': day_sales
            })
    
    selected_day_name = selected_date.strftime('%A')
    selected_day_date = selected_date.strftime('%Y-%m-%d')
    
    return render_template('sales/list_sales.html',
                         sales_by_barber=sales_by_barber,
                         week_days=week_days,
                         selected_day_name=selected_day_name,
                         selected_day_date=selected_day_date)

@sales_bp.route('/edit/<int:sale_id>', methods=['GET', 'POST'])
@login_required
def edit_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    
    if request.method == 'POST':
        new_amount = float(request.form.get('amount'))
        # If amount changed, store original and mark as updated
        if new_amount != sale.amount:
            sale.original_amount = sale.amount
            sale.status = 'updated'
        sale.amount = new_amount
        sale.barber_id = int(request.form.get('barber_id'))
        sale.service_id = int(request.form.get('service_id'))
        sale.payment_method = request.form.get('payment_method')
        sale.sale_date = datetime.strptime(request.form.get('sale_date'), '%Y-%m-%d').date()
        sale.notes = request.form.get('notes')
        
        db.session.commit()
        flash('Sale updated successfully (barber will see changes).', 'success')
        return redirect(url_for('sales.list_sales'))
    
    barbers = Barber.query.filter_by(active=True).all()
    services = Service.query.filter_by(active=True).all()
    return render_template('sales/edit_sale.html', sale=sale, barbers=barbers, services=services)

@sales_bp.route('/delete/<int:sale_id>')
@login_required
def delete_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    # Soft delete – only mark as deleted, do not remove from DB
    sale.status = 'deleted'
    db.session.commit()
    flash('Sale marked as deleted (barber will see it crossed out).', 'success')
    return redirect(url_for('sales.list_sales'))