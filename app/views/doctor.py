from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime, timedelta
import bcrypt

from app.models.doctors import Doctor, DoctorAvailability
from app.models.appointments import Appointment
from app.models.prescriptions import Prescription
from app.models.students import Student
from app.models.medications import Medication
from app.utils.helpers import log_activity, check_permission
from app.utils.database import get_db_connection

doctor = Blueprint('doctor', __name__)

@doctor.before_request
def check_doctor_auth():
    """Check if user is authenticated as a doctor."""
    if 'user_id' not in session or session.get('role') != 'doctor':
        flash('Please log in as a doctor to access this page.', 'danger')
        return redirect(url_for('auth.login'))

@doctor.route('/dashboard')
def dashboard():
    """Doctor dashboard route."""
    doctor_id = session.get('user_id')
    
    # Get doctor details
    doctor_details = Doctor.get_by_id(doctor_id)
    
    # Get today's date
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    # Get statistics for dashboard
    stats = {
        'appointments_today': len(Appointment.get_by_doctor(doctor_id, date=current_date)),
        'pending_appointments': len(Appointment.get_by_doctor(doctor_id, status='Scheduled')),
        'prescriptions_issued': len(Prescription.get_by_doctor(doctor_id)),
        'patients_seen': len(set([appt['StudentID'] for appt in Appointment.get_by_doctor(doctor_id, status='Completed')]))
    }
    
    # Get recent activities
    activities = []
    
    # Get upcoming appointments
    upcoming_appointments = Appointment.get_by_doctor(doctor_id, status='Scheduled')
    
    return render_template(
        'doctor/dashboard.html',
        doctor=doctor_details,
        stats=stats,
        activities=activities,
        upcoming_appointments=upcoming_appointments,
        current_date=datetime.now().strftime('%B %d, %Y')
    )

@doctor.route('/appointments')
def appointments():
    """Doctor appointments route."""
    doctor_id = session.get('user_id')
    
    # Get doctor details
    doctor_details = Doctor.get_by_id(doctor_id)
    
    # Get all appointments for this doctor
    appointments_list = Appointment.get_by_doctor(doctor_id)
    
    return render_template(
        'doctor/appointments.html',
        doctor=doctor_details,
        appointments=appointments_list
    )

@doctor.route('/view_appointment/<int:appointment_id>')
def view_appointment(appointment_id):
    """View a specific appointment."""
    doctor_id = session.get('user_id')
    
    # Get appointment details
    appointment = Appointment.get_by_id(appointment_id)
    
    # Check if appointment exists and belongs to this doctor
    if not appointment or appointment['DoctorID'] != doctor_id:
        flash('Appointment not found or access denied.', 'danger')
        return redirect(url_for('doctor.appointments'))
    
    # Get student details
    student = Student.get_by_id(appointment['StudentID'])
    
    # Get prescriptions for this appointment
    prescriptions = Prescription.get_by_appointment(appointment_id)
    
    # Get all medications for prescription form
    medications = Medication.get_all()
    
    return render_template(
        'doctor/view_appointment.html',
        appointment=appointment,
        student=student,
        prescriptions=prescriptions,
        medications=medications
    )

@doctor.route('/update_appointment/<int:appointment_id>', methods=['POST'])
def update_appointment(appointment_id):
    """Update appointment status."""
    doctor_id = session.get('user_id')
    
    # Get appointment details
    appointment = Appointment.get_by_id(appointment_id)
    
    # Check if appointment exists and belongs to this doctor
    if not appointment or appointment['DoctorID'] != doctor_id:
        flash('Appointment not found or access denied.', 'danger')
        return redirect(url_for('doctor.appointments'))
    
    # Get status from form
    status = request.form.get('status')
    
    # Update appointment status
    result = Appointment.update(appointment_id, {'Status': status})
    
    if result > 0:
        flash('Appointment status updated successfully.', 'success')
        log_activity('update_appointment', f'Updated appointment {appointment_id} status to {status}')
    else:
        flash('Failed to update appointment status.', 'danger')
    
    return redirect(url_for('doctor.view_appointment', appointment_id=appointment_id))

@doctor.route('/availability')
def availability():
    """Doctor availability management route."""
    doctor_id = session.get('user_id')
    
    # Get doctor details
    doctor_details = Doctor.get_by_id(doctor_id)
    
    # Get all availability records for this doctor
    availabilities = DoctorAvailability.get_by_doctor(doctor_id)
    
    return render_template(
        'doctor/availability.html',
        doctor=doctor_details,
        availabilities=availabilities
    )

@doctor.route('/add_availability', methods=['POST'])
def add_availability():
    """Add new availability."""
    doctor_id = session.get('user_id')
    
    # Get form data
    availability_date = request.form.get('availability_date')
    start_time = request.form.get('start_time')
    end_time = request.form.get('end_time')
    status = request.form.get('status')
    
    # Validate inputs
    if not availability_date or not start_time or not end_time:
        flash('Please fill all required fields.', 'danger')
        return redirect(url_for('doctor.availability'))
    
    # Create new availability record
    result = DoctorAvailability.create(doctor_id, availability_date, start_time, end_time, status)
    
    if result > 0:
        flash('Availability added successfully.', 'success')
        log_activity('add_availability', f'Added availability for {availability_date}')
    else:
        flash('Failed to add availability.', 'danger')
    
    return redirect(url_for('doctor.availability'))

@doctor.route('/edit_availability/<int:availability_id>', methods=['GET', 'POST'])
def edit_availability(availability_id):
    """Edit availability."""
    doctor_id = session.get('user_id')
    
    # Get availability record
    availability = DoctorAvailability.get_by_id(availability_id)
    
    # Check if availability exists and belongs to this doctor
    if not availability or availability['DoctorID'] != doctor_id:
        flash('Availability record not found or access denied.', 'danger')
        return redirect(url_for('doctor.availability'))
    
    if request.method == 'POST':
        # Get form data
        availability_date = request.form.get('availability_date')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        status = request.form.get('status')
        
        # Validate inputs
        if not availability_date or not start_time or not end_time:
            flash('Please fill all required fields.', 'danger')
            return render_template('doctor/edit_availability.html', availability=availability)
        
        # Update availability record
        data = {
            'AvailabilityDate': availability_date,
            'StartTime': start_time,
            'EndTime': end_time,
            'Status': status
        }
        
        result = DoctorAvailability.update(availability_id, data)
        
        if result > 0:
            flash('Availability updated successfully.', 'success')
            log_activity('update_availability', f'Updated availability for {availability_date}')
            return redirect(url_for('doctor.availability'))
        else:
            flash('Failed to update availability.', 'danger')
    
    return render_template('doctor/edit_availability.html', availability=availability)

@doctor.route('/delete_availability/<int:availability_id>')
def delete_availability(availability_id):
    """Delete availability."""
    doctor_id = session.get('user_id')
    
    # Get availability record
    availability = DoctorAvailability.get_by_id(availability_id)
    
    # Check if availability exists and belongs to this doctor
    if not availability or availability['DoctorID'] != doctor_id:
        flash('Availability record not found or access denied.', 'danger')
        return redirect(url_for('doctor.availability'))
    
    # Delete availability record
    result = DoctorAvailability.delete(availability_id)
    
    if result > 0:
        flash('Availability deleted successfully.', 'success')
        log_activity('delete_availability', f'Deleted availability for {availability["AvailabilityDate"]}')
    else:
        flash('Failed to delete availability.', 'danger')
    
    return redirect(url_for('doctor.availability'))

@doctor.route('/prescriptions')
def prescriptions():
    """Doctor prescriptions route."""
    doctor_id = session.get('user_id')
    
    # Get doctor details
    doctor_details = Doctor.get_by_id(doctor_id)
    
    # Get all prescriptions by this doctor
    prescriptions_list = Prescription.get_by_doctor(doctor_id)
    
    # Get all students and medications for the form
    students = Student.get_all()
    medications = Medication.get_all()
    
    # Get recent appointments for the form
    appointments = Appointment.get_by_doctor(doctor_id, status='Completed')
    
    return render_template(
        'doctor/prescriptions.html',
        doctor=doctor_details,
        prescriptions=prescriptions_list,
        students=students,
        medications=medications,
        appointments=appointments
    )

@doctor.route('/add_prescription', methods=['POST'])
def add_prescription():
    """Add new prescription."""
    doctor_id = session.get('user_id')
    
    # Get form data
    student_id = request.form.get('student_id')
    appointment_id = request.form.get('appointment_id') or None
    medication_id = request.form.get('medication_id')
    quantity = request.form.get('quantity')
    instructions = request.form.get('instructions')
    
    # Validate inputs
    if not student_id or not medication_id or not quantity or not instructions:
        flash('Please fill all required fields.', 'danger')
        return redirect(url_for('doctor.prescriptions'))
    
    # Create new prescription
    prescription_date = datetime.now().strftime('%Y-%m-%d')
    
    result = Prescription.create(
        appointment_id, doctor_id, student_id, medication_id,
        prescription_date, quantity, instructions
    )
    
    if result > 0:
        flash('Prescription added successfully.', 'success')
        log_activity('add_prescription', f'Added prescription for student {student_id}')
    else:
        flash('Failed to add prescription.', 'danger')
    
    return redirect(url_for('doctor.prescriptions'))
