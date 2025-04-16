from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime, timedelta

from app.models.staff import Staff
from app.models.prescriptions import Prescription, MedicineGiven
from app.models.medications import Medication
from app.models.students import Student
from app.utils.helpers import log_activity, check_permission
from app.utils.database import get_db_connection

staff = Blueprint('staff', __name__)

@staff.before_request
def check_staff_auth():
    """Check if user is authenticated as staff."""
    if 'user_id' not in session or session.get('role') != 'staff':
        flash('Please log in as staff to access this page.', 'danger')
        return redirect(url_for('auth.login'))

@staff.route('/dashboard')
def dashboard():
    """Staff dashboard route."""
    staff_id = session.get('user_id')
    
    # Get staff details
    staff_details = Staff.get_by_id(staff_id)
    
    # Get today's date
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    # Get statistics for dashboard
    stats = {
        'pending_prescriptions': len(Prescription.get_unfulfilled()),
        'low_stock_medications': len(Medication.get_low_stock()),
        'medicines_dispensed_today': len(MedicineGiven.get_by_date(current_date)),
        'total_students_served': len(set([p['StudentID'] for p in Prescription.get_all()]))
    }
    
    # Get recent activities
    activities = []
    
    # Get pending prescriptions
    pending_prescriptions = Prescription.get_unfulfilled()
    
    return render_template(
        'staff/dashboard.html',
        staff=staff_details,
        stats=stats,
        activities=activities,
        pending_prescriptions=pending_prescriptions,
        current_date=datetime.now().strftime('%B %d, %Y')
    )

@staff.route('/dispensary')
def dispensary():
    """Staff dispensary route."""
    staff_id = session.get('user_id')
    
    # Get staff details
    staff_details = Staff.get_by_id(staff_id)
    
    # Get all medications
    medications = Medication.get_all()
    
    # Get low stock medications
    low_stock_medications = Medication.get_low_stock()
    
    # Get expired medications
    current_date = datetime.now().strftime('%Y-%m-%d')
    expired_medications = Medication.get_expired(current_date)
    
    return render_template(
        'staff/dispensary.html',
        staff=staff_details,
        medications=medications,
        low_stock_medications=low_stock_medications,
        expired_medications=expired_medications,
        current_date=current_date
    )

@staff.route('/add_medication', methods=['POST'])
@staff.route('/add_medication', methods=['POST'])
def add_medication():
    """Add new medication."""
    # Get form data
    name = request.form.get('name')
    dosage_form = request.form.get('dosage_form')
    quantity = request.form.get('quantity')
    expiry_date = request.form.get('expiry_date') or None
    
    # Validate inputs
    if not name or not dosage_form or not quantity:
        flash('Please fill all required fields.', 'danger')
        return redirect(url_for('staff.dispensary'))
    
    # Create new medication
    result = Medication.create(name, dosage_form, quantity, expiry_date)
    
    if result > 0:
        flash('Medication added successfully.', 'success')
        log_activity('add_medication', f'Added medication: {name}')
    else:
        flash('Failed to add medication.', 'danger')
    
    return redirect(url_for('staff.dispensary'))

@staff.route('/edit_medication/<int:medication_id>', methods=['GET', 'POST'])
def edit_medication(medication_id):
    """Edit medication."""
    # Get medication details
    medication = Medication.get_by_id(medication_id)
    
    if not medication:
        flash('Medication not found.', 'danger')
        return redirect(url_for('staff.dispensary'))
    
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        dosage_form = request.form.get('dosage_form')
        quantity = request.form.get('quantity')
        expiry_date = request.form.get('expiry_date') or None
        
        # Validate inputs
        if not name or not dosage_form or not quantity:
            flash('Please fill all required fields.', 'danger')
            return render_template('staff/edit_medication.html', medication=medication)
        
        # Update medication
        data = {
            'Name': name,
            'DosageForm': dosage_form,
            'QuantityInStock': quantity,
            'ExpiryDate': expiry_date
        }
        
        result = Medication.update(medication_id, data)
        
        if result > 0:
            flash('Medication updated successfully.', 'success')
            log_activity('update_medication', f'Updated medication: {name}')
            return redirect(url_for('staff.dispensary'))
        else:
            flash('Failed to update medication.', 'danger')
    
    return render_template('staff/edit_medication.html', medication=medication)

@staff.route('/update_medication_stock', methods=['POST'])
def update_medication_stock():
    """Update medication stock."""
    if request.is_json:
        data = request.get_json()
        medication_id = data.get('medication_id')
        stock_change = data.get('stock_change')
    else:
        medication_id = request.form.get('medication_id')
        stock_change = request.form.get('stock_change')
    
    # Validate inputs
    if not medication_id or stock_change is None:
        if request.is_json:
            return jsonify({'success': False, 'message': 'Missing required fields.'})
        else:
            flash('Missing required fields.', 'danger')
            return redirect(url_for('staff.dispensary'))
    
    try:
        stock_change = int(stock_change)
    except ValueError:
        if request.is_json:
            return jsonify({'success': False, 'message': 'Stock change must be a number.'})
        else:
            flash('Stock change must be a number.', 'danger')
            return redirect(url_for('staff.dispensary'))
    
    # Update medication stock
    result = Medication.update_stock(medication_id, stock_change)
    
    if result > 0:
        if request.is_json:
            return jsonify({'success': True, 'message': 'Stock updated successfully.'})
        else:
            flash('Stock updated successfully.', 'success')
            log_activity('update_stock', f'Updated medication stock: ID {medication_id}, Change: {stock_change}')
    else:
        if request.is_json:
            return jsonify({'success': False, 'message': 'Failed to update stock. Check if there is enough stock to remove.'})
        else:
            flash('Failed to update stock. Check if there is enough stock to remove.', 'danger')
    
    return redirect(url_for('staff.dispensary'))

@staff.route('/prescriptions')
def prescriptions():
    """Staff prescriptions route."""
    staff_id = session.get('user_id')
    
    # Get staff details
    staff_details = Staff.get_by_id(staff_id)
    
    # Get pending prescriptions
    pending_prescriptions = Prescription.get_unfulfilled()
    
    # Get dispensed medications
    dispensed_medications = MedicineGiven.get_all()
    
    return render_template(
        'staff/prescriptions.html',
        staff=staff_details,
        pending_prescriptions=pending_prescriptions,
        dispensed_medications=dispensed_medications
    )

@staff.route('/dispense_medicine/<int:prescription_id>', methods=['GET', 'POST'])
def dispense_medicine(prescription_id):
    """Dispense medicine for a prescription."""
    # Get prescription details
    prescription = Prescription.get_by_id(prescription_id)
    
    if not prescription:
        flash('Prescription not found.', 'danger')
        return redirect(url_for('staff.prescriptions'))
    
    if request.method == 'POST':
        # Get form data
        quantity_given = request.form.get('quantity_given')
        
        # Validate inputs
        if not quantity_given:
            flash('Please enter quantity to dispense.', 'danger')
            return render_template('staff/dispense_medicine.html', prescription=prescription)
        
        try:
            quantity_given = int(quantity_given)
            if quantity_given <= 0 or quantity_given > prescription['Quantity']:
                flash('Invalid quantity. Must be between 1 and the prescribed quantity.', 'danger')
                return render_template('staff/dispense_medicine.html', prescription=prescription)
        except ValueError:
            flash('Quantity must be a number.', 'danger')
            return render_template('staff/dispense_medicine.html', prescription=prescription)
        
        # Create medicine given record
        date_given = datetime.now().strftime('%Y-%m-%d')
        
        result = MedicineGiven.create(
            prescription_id, 
            prescription['MedicationID'], 
            date_given, 
            quantity_given
        )
        
        if result > 0:
            flash('Medicine dispensed successfully.', 'success')
            log_activity('dispense_medicine', f'Dispensed medication for prescription {prescription_id}')
            return redirect(url_for('staff.prescriptions'))
        elif result == -1:
            flash('Failed to dispense medicine. Not enough stock available.', 'danger')
        else:
            flash('Failed to dispense medicine.', 'danger')
    
    return render_template('staff/dispense_medicine.html', prescription=prescription)

@staff.route('/api/medicines/dispense', methods=['POST'])
def api_dispense_medicine():
    """API endpoint to dispense medicine."""
    # Get form data
    prescription_id = request.form.get('prescription_id')
    medication_id = request.form.get('medication_id')
    quantity_given = request.form.get('quantity_given')
    
    # Validate inputs
    if not prescription_id or not medication_id or not quantity_given:
        return jsonify({'success': False, 'message': 'Missing required fields.'})
    
    try:
        prescription_id = int(prescription_id)
        medication_id = int(medication_id)
        quantity_given = int(quantity_given)
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid input values.'})
    
    # Get prescription details
    prescription = Prescription.get_by_id(prescription_id)
    
    if not prescription:
        return jsonify({'success': False, 'message': 'Prescription not found.'})
    
    if quantity_given <= 0 or quantity_given > prescription['Quantity']:
        return jsonify({'success': False, 'message': 'Invalid quantity. Must be between 1 and the prescribed quantity.'})
    
    # Create medicine given record
    date_given = datetime.now().strftime('%Y-%m-%d')
    
    result = MedicineGiven.create(
        prescription_id, 
        medication_id, 
        date_given, 
        quantity_given
    )
    
    if result > 0:
        log_activity('dispense_medicine', f'Dispensed medication for prescription {prescription_id}')
        return jsonify({'success': True, 'message': 'Medicine dispensed successfully.'})
    elif result == -1:
        return jsonify({'success': False, 'message': 'Failed to dispense medicine. Not enough stock available.'})
    else:
        return jsonify({'success': False, 'message': 'Failed to dispense medicine.'})

