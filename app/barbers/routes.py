from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required
from app.extensions import db
from app.barbers import barbers_bp
from app.forms import BarberForm, BorrowForm
from app.models import Barber, BarberAdvance

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
    
    advances = BarberAdvance.query.filter_by(settled=False).order_by(BarberAdvance.advance_date.desc()).all()
    return render_template('borrow/borrow_record.html', form=form, advances=advances)