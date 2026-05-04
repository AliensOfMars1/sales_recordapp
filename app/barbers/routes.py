from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.barbers import barbers_bp
from app.forms import BarberForm, BorrowForm
from app.models import Barber, BarberAdvance, Sale, Admin
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# ========== BARBER MANAGEMENT (ADMIN) ==========
@barbers_bp.route('/manage', methods=['GET', 'POST'])
@login_required
def manage_barbers():
    form = BarberForm()
    
    if form.validate_on_submit():
        barber = Barber(
            name=form.name.data,
            phone=form.phone.data,
            email=form.email.data,
            active=form.active.data
        )
        db.session.add(barber)
        db.session.commit()
        flash(f'Barber "{barber.name}" added successfully!', 'success')
        return redirect(url_for('barbers.manage_barbers'))
    
    barbers = Barber.query.order_by(Barber.name).all()
    return render_template('barbers/manage_barbers.html', form=form, barbers=barbers)


@barbers_bp.route('/edit/<int:barber_id>', methods=['POST'])
@login_required
def edit_barber(barber_id):
    barber = Barber.query.get_or_404(barber_id)
    
    # Get data from form
    barber.name = request.form.get('name')
    barber.phone = request.form.get('phone')
    barber.email = request.form.get('email')
    barber.active = request.form.get('active') == 'true'
    
    db.session.commit()
    flash('Barber updated successfully!', 'success')
    return redirect(url_for('barbers.manage_barbers'))


@barbers_bp.route('/delete/<int:barber_id>')
@login_required
def delete_barber(barber_id):
    barber = Barber.query.get_or_404(barber_id)
    db.session.delete(barber)
    db.session.commit()
    flash('Barber deleted successfully!', 'success')
    return redirect(url_for('barbers.manage_barbers'))


# ========== BARBER DASHBOARD ==========
@barbers_bp.route('/today-sales')
@login_required
def today_sales():
    if not isinstance(current_user, Barber):
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))
    
    barber = current_user
    date_str = request.args.get('date')
    if date_str:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        target_date = datetime.now().date()
    
    all_sales = Sale.query.filter(
        Sale.barber_id == barber.id,
        Sale.sale_date == target_date
    ).order_by(Sale.created_at.desc()).all()
    
    active_sales = [s for s in all_sales if s.status != 'deleted']
    total = sum(s.amount for s in active_sales)
    today_commission = total / 3
    today_cash = sum(s.amount for s in active_sales if s.payment_method == 'cash')
    today_momo = sum(s.amount for s in active_sales if s.payment_method == 'momo')
    
    for sale in all_sales:
        time_diff = datetime.now() - sale.created_at
        sale.is_new = time_diff.total_seconds() < 600
    
    return render_template('barbers/today_sales.html',
                         sales=all_sales,
                         total=total,
                         today_total=total,
                         today_commission=today_commission,
                         today_cash=today_cash,
                         today_momo=today_momo,
                         selected_date=target_date.strftime('%Y-%m-%d'))


@barbers_bp.route('/weekly-sales')
@login_required
def weekly_sales():
    if not isinstance(current_user, Barber):
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))
    
    barber = current_user
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    week_data = []
    week_total = 0
    week_cash = 0
    week_momo = 0
    
    for i in range(7):
        day_date = week_start + timedelta(days=i)
        # Exclude deleted sales
        sales = Sale.query.filter(
            Sale.barber_id == barber.id,
            Sale.sale_date == day_date,
            Sale.status.in_(['active', 'updated'])
        ).all()
        day_total = sum(s.amount for s in sales)
        day_cash = sum(s.amount for s in sales if s.payment_method == 'cash')
        day_momo = sum(s.amount for s in sales if s.payment_method == 'momo')
        week_total += day_total
        week_cash += day_cash
        week_momo += day_momo
        week_data.append({
            'name': days[i],
            'date': day_date.strftime('%Y-%m-%d'),
            'sales': day_total,
            'cash': day_cash,
            'momo': day_momo
        })
    
    week_commission = week_total / 3
    week_advances = sum(a.remaining_balance for a in barber.advances 
                        if not a.settled and week_start <= a.advance_date <= (week_start + timedelta(days=6)))
    week_net_payout = week_commission - week_advances
    
    return render_template('barbers/weekly_sales.html',
                         week_data=week_data,
                         week_total=week_total,
                         week_commission=week_commission,
                         week_advances=week_advances,
                         week_net_payout=week_net_payout)


@barbers_bp.route('/history')
@login_required
def history():
    if not isinstance(current_user, Barber):
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))
    
    barber = current_user
    today = datetime.now().date()
    
    selected_month_str = request.args.get('month')
    if selected_month_str:
        selected_month = datetime.strptime(selected_month_str, '%Y-%m').date()
    else:
        selected_month = today.replace(day=1)
    
    month_start = selected_month.replace(day=1)
    if month_start.month == 12:
        month_end = month_start.replace(year=month_start.year+1, month=1, day=1) - timedelta(days=1)
    else:
        month_end = month_start.replace(month=month_start.month+1, day=1) - timedelta(days=1)
    
    # Totals for selected month (exclude deleted)
    month_sales_q = Sale.query.filter(
        Sale.barber_id == barber.id,
        Sale.sale_date >= month_start,
        Sale.sale_date <= month_end,
        Sale.status.in_(['active', 'updated'])
    ).all()
    total_sales = sum(s.amount for s in month_sales_q)
    total_commission = total_sales / 3
    
    month_advances_q = BarberAdvance.query.filter(
        BarberAdvance.barber_id == barber.id,
        BarberAdvance.settled == False,
        BarberAdvance.advance_date >= month_start,
        BarberAdvance.advance_date <= month_end
    ).all()
    total_advances = sum(a.remaining_balance for a in month_advances_q)
    net_payout = total_commission - total_advances
    
    # Weekly breakdown (exclude deleted)
    weekly_breakdown = []
    current_week_start = month_start
    week_counter = 1
    while current_week_start <= month_end:
        week_end = current_week_start + timedelta(days=6)
        if week_end > month_end:
            week_end = month_end
        
        week_sales = Sale.query.filter(
            Sale.barber_id == barber.id,
            Sale.sale_date >= current_week_start,
            Sale.sale_date <= week_end,
            Sale.status.in_(['active', 'updated'])
        ).all()
        week_total = sum(s.amount for s in week_sales)
        week_commission = week_total / 3
        
        week_advances = BarberAdvance.query.filter(
            BarberAdvance.barber_id == barber.id,
            BarberAdvance.settled == False,
            BarberAdvance.advance_date >= current_week_start,
            BarberAdvance.advance_date <= week_end
        ).all()
        week_adv_total = sum(a.remaining_balance for a in week_advances)
        
        month_abbr = current_week_start.strftime('%b')
        week_label = f"{month_abbr} W{week_counter}"
        weekly_breakdown.append({
            'label': week_label,
            'sales': week_total,
            'commission': week_commission,
            'advances': week_adv_total
        })
        
        current_week_start = week_end + timedelta(days=1)
        week_counter += 1
    
    # Data for last 6 months (exclude deleted)
    months_labels = []
    months_commission = []
    for i in range(5, -1, -1):
        month_date = today.replace(day=1) - relativedelta(months=i)
        month_start_dt = month_date
        if month_start_dt.month == 12:
            month_end_dt = month_start_dt.replace(year=month_start_dt.year+1, month=1, day=1) - timedelta(days=1)
        else:
            month_end_dt = month_start_dt.replace(month=month_start_dt.month+1, day=1) - timedelta(days=1)
        
        month_sales = Sale.query.filter(
            Sale.barber_id == barber.id,
            Sale.sale_date >= month_start_dt,
            Sale.sale_date <= month_end_dt,
            Sale.status.in_(['active', 'updated'])
        ).all()
        month_total = sum(s.amount for s in month_sales)
        month_comm = month_total / 3
        
        months_labels.append(month_start_dt.strftime('%b %Y'))
        months_commission.append(month_comm)
    
    return render_template('barbers/history.html',
                         month_name=selected_month.strftime('%B %Y'),
                         total_sales=total_sales,
                         total_commission=total_commission,
                         total_advances=total_advances,
                         net_payout=net_payout,
                         weekly_breakdown=weekly_breakdown,
                         months_labels=months_labels,
                         months_commission=months_commission,
                         selected_month=selected_month.strftime('%Y-%m'))


@barbers_bp.route('/barber-dashboard')
@login_required
def barber_dashboard():
    return redirect(url_for('barbers.today_sales'))


# ========== ADMIN SET BARBER PASSWORD ==========
@barbers_bp.route('/set-password/<int:barber_id>', methods=['GET', 'POST'])
@login_required
def set_barber_password(barber_id):
    if not isinstance(current_user, Admin):
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    barber = Barber.query.get_or_404(barber_id)
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        if not password:
            flash('Password is required', 'danger')
        elif password != confirm:
            flash('Passwords do not match', 'danger')
        elif len(password) < 4:
            flash('Password must be at least 4 characters', 'danger')
        else:
            barber.set_password(password)
            db.session.commit()
            flash(f'Password set for {barber.name}. Barber can now log in.', 'success')
            return redirect(url_for('barbers.manage_barbers'))
    
    return render_template('barbers/set_password.html', barber=barber)


# ========== ADVANCES / BORROWING (ADMIN) ==========
@barbers_bp.route('/borrow', methods=['GET', 'POST'])
@login_required
def borrow_record():
    form = BorrowForm()
    
    if form.validate_on_submit():
        advance = BarberAdvance(
            barber_id=form.barber_id.data,
            amount=form.amount.data,
            advance_date=form.advance_date.data,
            note=form.note.data
        )
        db.session.add(advance)
        db.session.commit()
        flash('Borrowing record added successfully!', 'success')
        return redirect(url_for('barbers.borrow_record'))
    
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    advances = BarberAdvance.query.filter(
        BarberAdvance.settled == False,
        BarberAdvance.advance_date >= week_start,
        BarberAdvance.advance_date <= week_end
    ).order_by(BarberAdvance.advance_date.desc()).all()
    
    barbers = Barber.query.filter_by(active=True).order_by(Barber.name).all()
    
    weeks = []
    for i in range(12):
        week_start_date = week_start - timedelta(weeks=i)
        week_end_date = week_start_date + timedelta(days=6)
        weeks.append({
            'start': week_start_date.strftime('%Y-%m-%d'),
            'end': week_end_date.strftime('%Y-%m-%d'),
            'label': f"{week_start_date.strftime('%b %d')} - {week_end_date.strftime('%b %d')}"
        })
    
    current_week_label = weeks[0]['label']
    
    return render_template('borrow/borrow_record.html',
                         form=form,
                         advances=advances,
                         barbers=barbers,
                         weeks=weeks,
                         current_week_label=current_week_label,
                         current_week_start=week_start.strftime('%Y-%m-%d'),
                         current_week_end=week_end.strftime('%Y-%m-%d'))


@barbers_bp.route('/get-advances-by-week')
@login_required
def get_advances_by_week():
    start_date_str = request.args.get('start')
    end_date_str = request.args.get('end')
    
    if not start_date_str or not end_date_str:
        return jsonify([])
    
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    
    advances = BarberAdvance.query.filter(
        BarberAdvance.advance_date >= start_date,
        BarberAdvance.advance_date <= end_date,
        BarberAdvance.settled == False
    ).order_by(BarberAdvance.advance_date.desc()).all()
    
    result = []
    for advance in advances:
        result.append({
            'id': advance.id,
            'date': advance.advance_date.strftime('%Y-%m-%d'),
            'barber_name': advance.barber.name,
            'amount': advance.amount,
            'settled_amount': advance.settled_amount,
            'remaining': advance.remaining_balance,
            'note': advance.note or '-'
        })
    
    return jsonify(result)


@barbers_bp.route('/edit-advance/<int:advance_id>', methods=['POST'])
@login_required
def edit_advance(advance_id):
    advance = BarberAdvance.query.get_or_404(advance_id)
    advance.barber_id = int(request.form.get('barber_id'))
    advance.amount = float(request.form.get('amount'))
    advance.advance_date = datetime.strptime(request.form.get('advance_date'), '%Y-%m-%d').date()
    advance.note = request.form.get('note')
    db.session.commit()
    flash('Advance updated successfully!', 'success')
    return redirect(url_for('barbers.borrow_record'))


@barbers_bp.route('/settle-advance/<int:advance_id>', methods=['POST'])
@login_required
def settle_advance(advance_id):
    advance = BarberAdvance.query.get_or_404(advance_id)
    settle_amount = float(request.form.get('settle_amount', 0))
    
    if settle_amount <= 0:
        flash('Please enter a valid settlement amount', 'danger')
        return redirect(url_for('barbers.borrow_record'))
    
    if settle_amount >= advance.remaining_balance:
        advance.settled_amount = advance.amount
        advance.settled = True
        flash('Advance fully settled! Remaining: GH₵0.00', 'success')
    else:
        advance.settled_amount += settle_amount
        flash(f'Partial settlement of GH₵{settle_amount:.2f} recorded. Remaining: GH₵{advance.remaining_balance:.2f}', 'success')
    
    db.session.commit()
    return redirect(url_for('barbers.borrow_record'))


@barbers_bp.route('/delete-advance/<int:advance_id>')
@login_required
def delete_advance(advance_id):
    advance = BarberAdvance.query.get_or_404(advance_id)
    db.session.delete(advance)
    db.session.commit()
    flash('Advance record deleted successfully!', 'success')
    return redirect(url_for('barbers.borrow_record'))