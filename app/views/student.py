from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime, timedelta

from app.models.students import Student
from app.models.doctors import Doctor, DoctorAvailability
from app.models.appointments import Appointment
from app.models.prescriptions import Prescription
from app.utils.helpers import log_activity, check_permission
from app.utils.database import get_db_connection
# from app.views.crud import get_doctor_availability
student = Blueprint('student', __name__)

@student.before_request
def check_student_auth():
    """Check if user is authenticated as a student."""
    if 'user_id' not in session or session.get('role') != 'student':
        flash('Please log in as a student to access this page.', 'danger')
        return redirect(url_for('auth.login'))

@student.route('/dashboard')
def dashboard():
    """Student dashboard route."""
    student_id = session.get('user_id')
    
    # Get student details
    student_details = Student.get_by_id(student_id)
    
    # Get today's date
    current_date = datetime.now().strftime('%Y-%m-%d')
    appointments = Appointment.get_by_student(student_id)
    upcoming_appointments = [a for a in appointments if a.status == 'Scheduled']
    # Get statistics for dashboard
    stats = {
        'upcoming_appointments': len(upcoming_appointments),
        'pending_prescriptions': len([p for p in Prescription.get_by_student(student_id) if not p.get('DateGiven')]),
        'total_appointments': len(Appointment.get_by_student(student_id)),
        'total_prescriptions': len(Prescription.get_by_student(student_id))
    }
    
    # Get upcoming appointments
    upcoming_appointments = [a for a in appointments if a.status == 'Scheduled']
    
    # Get recent prescriptions
    recent_prescriptions = Prescription.get_by_student(student_id)[:5]  # Get only the 5 most recent
    
    return render_template(
        'student/dashboard.html',
        student=student_details,
        stats=stats,
        upcoming_appointments=upcoming_appointments,
        recent_prescriptions=recent_prescriptions,
        current_date=datetime.now().strftime('%B %d, %Y')
    )

@student.route('/doctors')
def doctors():
    """Student doctors route."""
    # Get all doctors
    doctors_list = Doctor.get_all()
    
    # Get availability for each doctor
    for doctor in doctors_list:
        doctor['availability'] = DoctorAvailability.get_by_doctor(doctor['DoctorID'])
    
    return render_template(
        'student/doctors.html',
        doctors=doctors_list
    )

@student.route('/appointments')
def appointments():
    """Student appointments route."""
    student_id = session.get('user_id')
    
    # Get all doctors for booking form
    doctors_list = Doctor.get_all()
    
    # Get current date
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    # Get upcoming appointments
    appointments = Appointment.get_by_student(student_id)
    upcoming_appointments = [a for a in appointments if a.status == 'Scheduled']
    
    # Get past appointments
    # past_appointments = Appointment.get_by_student(student_id, status=['Completed', 'Cancelled'])
    past_appointments = [a for a in appointments if a in ['Completed', 'Cancelled']]
    return render_template(
        'student/appointments.html',
        doctors=doctors_list,
        upcoming_appointments=upcoming_appointments,
        past_appointments=past_appointments,
        current_date=current_date
    )

@student.route('/book_appointment', methods=['POST'])
def book_appointment():
    """Book a new appointment."""
    student_id = session.get('user_id')
    
    # Get form data
    doctor_id = request.form.get('doctor_id')
    appointment_date = request.form.get('appointment_date')
    appointment_time = request.form.get('appointment_time')
    problem_description = request.form.get('problem_description')
    
    # Validate inputs
    if not doctor_id or not appointment_date or not appointment_time:
        if request.is_json:
            return jsonify({'success': False, 'message': 'Missing required fields.'})
        else:
            flash('Please fill all required fields.', 'danger')
            return redirect(url_for('student.appointments'))
    
    # Check if slot is available
    available_slots = DoctorAvailability.get_available_slots(doctor_id, appointment_date)
    slot_available = False
    
    for slot in available_slots:
        if slot['time'] == appointment_time and slot['status'] == 'Available':
            slot_available = True
            break
    
    if not slot_available:
        if request.is_json:
            return jsonify({'success': False, 'message': 'Selected time slot is not available.'})
        else:
            flash('Selected time slot is not available.', 'danger')
            return redirect(url_for('student.appointments'))
    
    # Create new appointment
    result = Appointment.create(
        student_id, 
        doctor_id, 
        appointment_date, 
        appointment_time, 
        'Scheduled'
    )
    
    if result > 0:
        if request.is_json:
            return jsonify({'success': True, 'message': 'Appointment booked successfully.'})
        else:
            flash('Appointment booked successfully.', 'success')
            log_activity('book_appointment', f'Booked appointment with doctor {doctor_id} on {appointment_date} at {appointment_time}')
    else:
        if request.is_json:
            return jsonify({'success': False, 'message': 'Failed to book appointment.'})
        else:
            flash('Failed to book appointment.', 'danger')
    
    return redirect(url_for('student.appointments'))

@student.route('/book_appointment_for_doctor/<int:doctor_id>', methods=['GET', 'POST'])
def book_appointment_for_doctor(doctor_id):
    """Show appointment booking page for a specific doctor and handle form submission."""
    student_id = session.get('user_id')
    
    # Get doctor details
    doctor = Doctor.get_by_id(doctor_id)
    
    if not doctor:
        flash('Doctor not found.', 'danger')
        return redirect(url_for('student.doctors'))
    
    # Handle form submission
    if request.method == 'POST':
        appointment_date = request.form.get('appointment_date')
        time_slot = request.form.get('time_slot')
        problem_description = request.form.get('problem_description')
        
        # Validate inputs
        if not appointment_date or not time_slot:
            flash('Please select both date and time for your appointment.', 'danger')
            # Get doctor's availability for rendering the form again
            availability = DoctorAvailability.get_by_doctor(doctor_id)
            today = datetime.now().strftime('%Y-%m-%d')
            return render_template(
                'student/book_appointment.html',
                doctor=doctor,
                availability=availability,
                today=today
            )
        
        # Create new appointment
        result = Appointment.create(
            student_id, 
            doctor_id, 
            appointment_date, 
            time_slot, 
            'Scheduled'
        )
        
        if result > 0:
            flash('Appointment booked successfully.', 'success')
            log_activity('book_appointment', f'Booked appointment with doctor {doctor_id} on {appointment_date} at {time_slot}')
            return redirect(url_for('student.appointments'))
        else:
            flash('Failed to book appointment.', 'danger')
            
    # GET request handling
    # Get doctor's availability
    availability = DoctorAvailability.get_by_doctor(doctor_id)
    today = datetime.now().strftime('%Y-%m-%d')
    
    return render_template(
        'student/book_appointment.html',
        doctor=doctor,
        availability=availability,
        today=today
    )

@student.route('/get_available_slots/<int:doctor_id>/<string:date>')
def get_available_slots(doctor_id, date):
    """Get available appointment slots for a doctor on a specific date."""
    try:
        # Validate inputs
        if not doctor_id or not date:
            return jsonify({"error": "Missing doctor ID or date"}), 400
            
        # Format the date properly if needed
        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%Y-%m-%d')
        except ValueError:
            return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD format."}), 400
            
        # Get all slots for the doctor on the given date
        availability_slots = DoctorAvailability.get_available_slots(
            doctor_id=doctor_id, 
            date=formatted_date
        )
        
        # Transform the data into the format expected by the frontend
        slots = []
        for slot in availability_slots:
            # Check if we have the expected keys
            if 'time' not in slot or 'status' not in slot:
                continue
                
            # Format the time value
            time_str = slot['time']
            time_parts = time_str.split(':')  # Split HH:MM:SS
            start_time = f"{time_parts[0]}:{time_parts[1]}"  # HH:MM
            
            slots.append({
                "StartTime": start_time,
                "Status": slot['status'].capitalize()  # Convert 'available' to 'Available'
            })
            
        return jsonify({"slots": slots})
    except Exception as e:
        # Log the full error details for debugging
        import traceback
        print(f"Error fetching slots: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@student.route('/cancel_appointment/<int:appointment_id>')
def cancel_appointment(appointment_id):
    """Cancel an appointment."""
    student_id = session.get('user_id')
    
    # Get appointment details
    appointment = Appointment.get_by_id(appointment_id)
    
    # Check if appointment exists and belongs to this student
    if not appointment or appointment['StudentID'] != student_id:
        flash('Appointment not found or access denied.', 'danger')
        return redirect(url_for('student.appointments'))
    
    # Update appointment status
    result = Appointment.update(appointment_id, {'Status': 'Cancelled'})
    
    if result > 0:
        flash('Appointment cancelled successfully.', 'success')
        log_activity('cancel_appointment', f'Cancelled appointment {appointment_id}')
    else:
        flash('Failed to cancel appointment.', 'danger')
    
    return redirect(url_for('student.appointments'))

@student.route('/prescriptions')
def prescriptions():
    """Student prescriptions route."""
    student_id = session.get('user_id')
    
    # Get all prescriptions for this student
    all_prescriptions = Prescription.get_by_student(student_id)
    
    # Separate current and past prescriptions
    current_date = datetime.now().date()
    three_months_ago = current_date - timedelta(days=90)
    
    current_prescriptions = []
    prescription_history = []
    
    for prescription in all_prescriptions:
        prescription_date = datetime.strptime(prescription['PrescriptionDate'], '%Y-%m-%d').date()
        
        if prescription_date >= three_months_ago:
            current_prescriptions.append(prescription)
        else:
            prescription_history.append(prescription)
    
    return render_template(
        'student/prescriptions.html',
        current_prescriptions=current_prescriptions,
        prescription_history=prescription_history
    )

@student.route('/api/appointments/availability', methods=['GET'])
def api_appointments_availability():
    """API endpoint to get available appointment slots."""
    doctor_id = request.args.get('doctor_id')
    date = request.args.get('date')
    
    if not doctor_id or not date:
        return jsonify({'success': False, 'message': 'Missing required parameters.'}), 400
    
    try:
        # Get available slots
        slots = DoctorAvailability.get_available_slots(doctor_id, date)
        
        # Format slots for frontend display
        formatted_slots = []
        for slot in slots:
            if 'time' not in slot or 'status' not in slot:
                continue
                
            # Format the time value
            time_str = slot['time']
            time_parts = time_str.split(':')  # Split HH:MM:SS
            start_time = f"{time_parts[0]}:{time_parts[1]}"  # HH:MM
            
            formatted_slots.append({
                "StartTime": start_time,
                "Status": slot['status'].capitalize()  # Convert 'available' to 'Available'
            })
        
        return jsonify({
            'success': True,
            'slots': formatted_slots
        })
    except Exception as e:
        print(f"Error fetching availability: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error fetching availability: {str(e)}'
        }), 500
