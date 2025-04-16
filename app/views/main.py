from flask import Blueprint, render_template, redirect, url_for, session, request, jsonify
from datetime import datetime, timedelta

from app.models.appointments import Appointment
from app.models.prescriptions import Prescription, MedicineGiven
from app.models.medications import Medication
from app.utils.helpers import log_activity, get_current_date

main = Blueprint('main', __name__)

@main.route('/')
def index():
    """
    Main index route.
    If user is logged in, redirect to appropriate dashboard.
    Otherwise, show login page.
    """
    if 'user_id' in session:
        role = session.get('role')
        
        if role == 'doctor':
            return redirect(url_for('doctor.dashboard'))
        elif role == 'staff':
            return redirect(url_for('staff.dashboard'))
        elif role == 'student':
            return redirect(url_for('student.dashboard'))
    
    return redirect(url_for('auth.login'))

@main.route('/about')
def about():
    """About page route."""
    return render_template('about.html')

@main.route('/contact')
def contact():
    """Contact page route."""
    return render_template('contact.html')

@main.route('/services')
def services():
    """Services page route."""
    return render_template('services.html')

@main.route('/emergency')
def emergency():
    """Emergency information page route."""
    return render_template('emergency.html')

@main.route('/faq')
def faq():
    """FAQ page route."""
    return render_template('faq.html')

@main.route('/api/dashboard/stats')
def api_dashboard_stats():
    """API endpoint to get dashboard statistics."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated.'})
    
    user_id = session.get('user_id')
    role = session.get('role')
    
    stats = {}
    
    if role == 'doctor':
        # Get today's date
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        stats = {
            'appointments_today': len(Appointment.get_by_doctor(user_id, date=current_date)),
            'pending_appointments': len(Appointment.get_by_doctor(user_id, status='Scheduled')),
            'prescriptions_issued': len(Prescription.get_by_doctor(user_id)),
            'patients_seen': len(set([appt['StudentID'] for appt in Appointment.get_by_doctor(user_id, status='Completed')]))
        }
    elif role == 'staff':
        # Get today's date
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        stats = {
            'pending_prescriptions': len(Prescription.get_unfulfilled()),
            'low_stock_medications': len(Medication.get_low_stock()),
            'medicines_dispensed_today': len(MedicineGiven.get_by_date(current_date)),
            'total_students_served': len(set([p['StudentID'] for p in Prescription.get_all()]))
        }
    elif role == 'student':
        stats = {
            'upcoming_appointments': len(Appointment.get_by_student(user_id)),
            'pending_prescriptions': len([p for p in Prescription.get_by_student(user_id) if not p.get('DateGiven')]),
            'total_appointments': len(Appointment.get_by_student(user_id)),
            'total_prescriptions': len(Prescription.get_by_student(user_id))
        }
    
    return jsonify({'success': True, 'stats': stats})

@main.route('/api/dashboard/activity')
def api_dashboard_activity():
    """API endpoint to get dashboard activity."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated.'})
    
    user_id = session.get('user_id')
    role = session.get('role')
    
    # Get activity logs
    activities = []
    
    # This would typically come from an ActivityLog table
    # For now, we'll return an empty list
    
    return jsonify({'success': True, 'activities': activities})

@main.route('/api/notifications')
def api_notifications():
    """API endpoint to get notifications."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated.'})
    
    user_id = session.get('user_id')
    role = session.get('role')
    
    # Get notifications
    notifications = []
    new_notifications = 0
    
    # This would typically come from a Notifications table
    # For now, we'll return an empty list
    
    return jsonify({
        'success': True, 
        'notifications': notifications,
        'new_notifications': new_notifications
    })

@main.route('/api/medications')
def api_medications():
    """API endpoint to get medications."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated.'})
    
    # Get all medications
    medications = Medication.get_all()
    
    return jsonify({'success': True, 'medications': medications})

@main.route('/api/appointments/<int:appointment_id>')
def api_appointment_details(appointment_id):
    """API endpoint to get appointment details."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated.'})
    
    # Get appointment details
    appointment = Appointment.get_by_id(appointment_id)
    
    if not appointment:
        return jsonify({'success': False, 'message': 'Appointment not found.'})
    
    return jsonify({'success': True, 'appointment': appointment})

@main.route('/api/prescriptions/<int:prescription_id>')
def api_prescription_details(prescription_id):
    """API endpoint to get prescription details."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated.'})
    
    # Get prescription details
    prescription = Prescription.get_by_id(prescription_id)
    
    if not prescription:
        return jsonify({'success': False, 'message': 'Prescription not found.'})
    
    return jsonify({'success': True, 'prescription': prescription})

@main.route('/api/appointments/<int:appointment_id>/is-owner')
def api_is_appointment_owner(appointment_id):
    """API endpoint to check if current user is the owner of an appointment."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated.'})
    
    user_id = session.get('user_id')
    role = session.get('role')
    
    # Get appointment details
    appointment = Appointment.get_by_id(appointment_id)
    
    if not appointment:
        return jsonify({'success': False, 'message': 'Appointment not found.'})
    
    is_owner = False
    
    if role == 'student' and str(appointment['StudentID']) == str(user_id):
        is_owner = True
    elif role == 'doctor' and str(appointment['DoctorID']) == str(user_id):
        is_owner = True
    
    return jsonify({'success': True, 'is_owner': is_owner})

@main.route('/api/appointments/<int:appointment_id>/complete', methods=['POST'])
def api_complete_appointment(appointment_id):
    """API endpoint to mark an appointment as completed."""
    if 'user_id' not in session or session.get('role') != 'doctor':
        return jsonify({'success': False, 'message': 'Not authorized.'})
    
    user_id = session.get('user_id')
    
    # Get appointment details
    appointment = Appointment.get_by_id(appointment_id)
    
    if not appointment:
        return jsonify({'success': False, 'message': 'Appointment not found.'})
    
    if str(appointment['DoctorID']) != str(user_id):
        return jsonify({'success': False, 'message': 'Not authorized to complete this appointment.'})
    
    # Update appointment status
    result = Appointment.update(appointment_id, {'Status': 'Completed'})
    
    if result > 0:
        log_activity('complete_appointment', f'Completed appointment {appointment_id}')
        return jsonify({'success': True, 'message': 'Appointment marked as completed.'})
    else:
        return jsonify({'success': False, 'message': 'Failed to complete appointment.'})

@main.route('/api/appointments/<int:appointment_id>/cancel', methods=['POST'])
def api_cancel_appointment(appointment_id):
    """API endpoint to cancel an appointment."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated.'})
    
    user_id = session.get('user_id')
    role = session.get('role')
    
    # Get appointment details
    appointment = Appointment.get_by_id(appointment_id)
    
    if not appointment:
        return jsonify({'success': False, 'message': 'Appointment not found.'})
    
    # Check if user is authorized to cancel this appointment
    if role == 'student' and str(appointment['StudentID']) != str(user_id):
        return jsonify({'success': False, 'message': 'Not authorized to cancel this appointment.'})
    elif role == 'doctor' and str(appointment['DoctorID']) != str(user_id):
        return jsonify({'success': False, 'message': 'Not authorized to cancel this appointment.'})
    
    # Update appointment status
    result = Appointment.update(appointment_id, {'Status': 'Cancelled'})
    
    if result > 0:
        log_activity('cancel_appointment', f'Cancelled appointment {appointment_id}')
        return jsonify({'success': True, 'message': 'Appointment cancelled successfully.'})
    else:
        return jsonify({'success': False, 'message': 'Failed to cancel appointment.'})

@main.route('/api/appointments/reschedule', methods=['POST'])
def api_reschedule_appointment():
    """API endpoint to reschedule an appointment."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated.'})
    
    user_id = session.get('user_id')
    role = session.get('role')
    
    # Get form data
    appointment_id = request.form.get('appointment_id')
    new_date = request.form.get('new_date')
    new_time = request.form.get('new_time')
    
    if not appointment_id or not new_date or not new_time:
        return jsonify({'success': False, 'message': 'Missing required fields.'})
    
    # Get appointment details
    appointment = Appointment.get_by_id(appointment_id)
    
    if not appointment:
        return jsonify({'success': False, 'message': 'Appointment not found.'})
    
    # Check if user is authorized to reschedule this appointment
    if role == 'student' and str(appointment['StudentID']) != str(user_id):
        return jsonify({'success': False, 'message': 'Not authorized to reschedule this appointment.'})
    elif role == 'doctor' and str(appointment['DoctorID']) != str(user_id):
        return jsonify({'success': False, 'message': 'Not authorized to reschedule this appointment.'})
    
    # Update appointment date and time
    data = {
        'AppointmentDate': new_date,
        'AppointmentTime': new_time
    }
    
    result = Appointment.update(appointment_id, data)
    
    if result > 0:
        log_activity('reschedule_appointment', f'Rescheduled appointment {appointment_id} to {new_date} at {new_time}')
        return jsonify({'success': True, 'message': 'Appointment rescheduled successfully.'})
    else:
        return jsonify({'success': False, 'message': 'Failed to reschedule appointment.'})

@main.route('/api/prescriptions/add', methods=['POST'])
def api_add_prescription():
    """API endpoint to add a prescription."""
    if 'user_id' not in session or session.get('role') != 'doctor':
        return jsonify({'success': False, 'message': 'Not authorized.'})
    
    doctor_id = session.get('user_id')
    
    # Get form data
    appointment_id = request.form.get('appointment_id')
    student_id = request.form.get('student_id')
    medication_id = request.form.get('medication_id')
    quantity = request.form.get('quantity')
    instructions = request.form.get('instructions')
    
    if not student_id or not medication_id or not quantity or not instructions:
        return jsonify({'success': False, 'message': 'Missing required fields.'})
    
    # Create new prescription
    prescription_date = get_current_date()
    
    result = Prescription.create(
        appointment_id, doctor_id, student_id, medication_id,
        prescription_date, quantity, instructions
    )
    
    if result > 0:
        log_activity('add_prescription', f'Added prescription for student {student_id}')
        return jsonify({'success': True, 'message': 'Prescription added successfully.'})
    else:
        return jsonify({'success': False, 'message': 'Failed to add prescription.'})

@main.route('/api/medicines/dispense', methods=['POST'])
def api_dispense_medicine():
    """API endpoint to dispense medicine."""
    if 'user_id' not in session or session.get('role') != 'staff':
        return jsonify({'success': False, 'message': 'Not authorized.'})
    
    # Get form data
    prescription_id = request.form.get('prescription_id')
    medication_id = request.form.get('medication_id')
    quantity_given = request.form.get('quantity_given')
    
    if not prescription_id or not medication_id or not quantity_given:
        return jsonify({'success': False, 'message': 'Missing required fields.'})
    
    try:
        quantity_given = int(quantity_given)
    except ValueError:
        return jsonify({'success': False, 'message': 'Quantity must be a number.'})
    
    # Create medicine given record
    date_given = get_current_date()
    
    result = MedicineGiven.create(
        prescription_id, medication_id, date_given, quantity_given
    )
    
    if result > 0:
        log_activity('dispense_medicine', f'Dispensed medicine for prescription {prescription_id}')
        return jsonify({'success': True, 'message': 'Medicine dispensed successfully.'})
    elif result == -1:
        return jsonify({'success': False, 'message': 'Failed to dispense medicine. Not enough stock available.'})
    else:
        return jsonify({'success': False, 'message': 'Failed to dispense medicine.'})
