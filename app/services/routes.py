from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required
from app.extensions import db
from app.services import services_bp
from app.forms import ServiceForm
from app.models import Service

@services_bp.route('/manage', methods=['GET', 'POST'])
@login_required
def manage_services():
    form = ServiceForm()
    
    if form.validate_on_submit():
        service = Service(
            name=form.name.data,
            default_price=form.default_price.data,
            description=form.description.data,
            active=form.active.data
        )
        db.session.add(service)
        db.session.commit()
        flash(f'Service "{service.name}" added successfully!', 'success')
        return redirect(url_for('services.manage_services'))
    
    services = Service.query.order_by(Service.name).all()
    return render_template('services/manage_services.html', form=form, services=services)

@services_bp.route('/edit/<int:service_id>', methods=['POST'])
@login_required
def edit_service(service_id):
    service = Service.query.get_or_404(service_id)
    service.name = request.form.get('name')
    service.default_price = float(request.form.get('default_price'))
    service.description = request.form.get('description')
    service.active = request.form.get('active') == 'true'
    db.session.commit()
    flash('Service updated successfully!', 'success')
    return redirect(url_for('services.manage_services'))

@services_bp.route('/delete/<int:service_id>')
@login_required
def delete_service(service_id):
    service = Service.query.get_or_404(service_id)
    db.session.delete(service)
    db.session.commit()
    flash('Service deleted successfully!', 'success')
    return redirect(url_for('services.manage_services'))