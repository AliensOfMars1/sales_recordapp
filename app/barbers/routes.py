from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required
from app.extensions import db
from app.barbers import barbers_bp
from app.forms import BarberForm, BorrowForm
from app.models import Barber, BarberAdvance
from datetime import datetime, timedelta

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
    
    # Get current week start (Monday)
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    
    # Get outstanding advances (not fully settled) for current week by default
    advances = BarberAdvance.query.filter(
        BarberAdvance.settled == False,
        BarberAdvance.advance_date >= week_start,
        BarberAdvance.advance_date <= week_end
    ).order_by(BarberAdvance.advance_date.desc()).all()
    
    # Get all active barbers for dropdown
    barbers = Barber.query.filter_by(active=True).order_by(Barber.name).all()
    
    # Get week options for filter
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
    """API endpoint to get advances for a specific week"""
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
        # Fully settled
        advance.settled_amount = advance.amount
        advance.settled = True
        flash(f'Advance fully settled! Remaining: GH₵0.00', 'success')
    else:
        # Partially settled
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