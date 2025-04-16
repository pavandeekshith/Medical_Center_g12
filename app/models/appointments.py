from app.utils.database import get_db_connection
from datetime import datetime

class Appointment:
    def __init__(self, appointment_id=None, student_id=None, doctor_id=None, 
                 appointment_date=None, appointment_time=None, status=None):
        self.appointment_id = appointment_id
        self.student_id = student_id
        self.doctor_id = doctor_id
        self.appointment_date = appointment_date
        self.appointment_time = appointment_time
        self.status = status
    
    @staticmethod
    def create(student_id, doctor_id, appointment_date, appointment_time, status='Scheduled'):
        """Create a new appointment."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Insert the new appointment
            cursor.execute(
                'INSERT INTO Appointments (StudentID, DoctorID, AppointmentDate, AppointmentTime, Status) '
                'VALUES (%s, %s, %s, %s, %s)',
                (student_id, doctor_id, appointment_date, appointment_time, status)
            )
            
            # Get the ID of the inserted appointment
            appointment_id = cursor.lastrowid
            
            conn.commit()
            conn.close()
            
            return appointment_id
        except Exception as e:
            print(f"Error creating appointment: {e}")
            return 0
    
    @staticmethod
    def get_all():
        """Get all appointments."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT a.*, s.FirstName || " " || s.LastName as StudentName, '
            'd.Name as DoctorName '
            'FROM Appointments a '
            'JOIN Students s ON a.StudentID = s.StudentID '
            'JOIN cs432cims.G12_Doctors d ON a.DoctorID = d.DoctorID '
            'ORDER BY a.AppointmentDate DESC, a.AppointmentTime DESC'
        )
        
        appointments = cursor.fetchall()
        conn.close()
        
        return appointments
    
    @staticmethod
    def get_by_id(appointment_id):
        """Get appointment by ID."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT a.*, s.FirstName || " " || s.LastName as StudentName, '
            'd.Name as DoctorName '
            'FROM Appointments a '
            'JOIN Students s ON a.StudentID = s.StudentID '
            'JOIN cs432cims.G12_Doctors d ON a.DoctorID = d.DoctorID '
            'WHERE a.AppointmentID = %s',
            (appointment_id,)
        )
        
        appointment = cursor.fetchone()
        conn.close()
        
        return appointment
    
    @staticmethod
    def get_by_student(student_id):
        """Get appointments by student ID."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT a.*, d.Name as DoctorName, d.Specialization, d.Email, d.ContactNumber '
            'FROM Appointments a '
            'JOIN cs432cims.G12_Doctors d ON a.DoctorID = d.DoctorID '
            'WHERE a.StudentID = %s '
            'ORDER BY a.AppointmentDate DESC, a.AppointmentTime DESC',
            (student_id,)
        )
        
        appointments = cursor.fetchall()
        conn.close()
        
        return appointments
    
    @staticmethod
    def get_by_doctor(doctor_id):
        """Get appointments by doctor ID."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT a.*, s.FirstName || " " || s.LastName as StudentName, '
            's.Email as StudentEmail, s.ContactNumber as StudentContact '
            'FROM Appointments a '
            'JOIN Students s ON a.StudentID = s.StudentID '
            'WHERE a.DoctorID = %s '
            'ORDER BY a.AppointmentDate DESC, a.AppointmentTime DESC',
            (doctor_id,)
        )
        
        appointments = cursor.fetchall()
        conn.close()
        
        return appointments
    
    @staticmethod
    def get_upcoming_by_student(student_id):
        """Get upcoming appointments by student ID."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute(
            'SELECT a.*, d.Name as DoctorName, d.Specialization '
            'FROM Appointments a '
            'JOIN cs432cims.G12_Doctors d ON a.DoctorID = d.DoctorID '
            'WHERE a.StudentID = %s AND (a.AppointmentDate > %s OR '
            '(a.AppointmentDate = %s AND a.AppointmentTime > %s)) '
            'AND a.Status = "Scheduled" '
            'ORDER BY a.AppointmentDate, a.AppointmentTime',
            (student_id, today, today, datetime.now().strftime('%H:%M'))
        )
        
        appointments = cursor.fetchall()
        conn.close()
        
        return appointments
    
    @staticmethod
    def update(appointment_id, data):
        """Update appointment details."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Build the SQL query based on the provided data
            query_parts = []
            values = []
            
            for key, value in data.items():
                query_parts.append(f"{key} = %s")
                values.append(value)
            
            # Add the appointment ID to the values
            values.append(appointment_id)
            
            # Execute the update query
            cursor.execute(
                f'UPDATE Appointments SET {", ".join(query_parts)} WHERE AppointmentID = %s',
                tuple(values)
            )
            
            # Check if any rows were affected
            affected_rows = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            return affected_rows
        except Exception as e:
            print(f"Error updating appointment: {e}")
            return 0
    
    @staticmethod
    def delete(appointment_id):
        """Delete an appointment."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM Appointments WHERE AppointmentID = %s', (appointment_id,))
            
            # Check if any rows were affected
            affected_rows = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            return affected_rows
        except Exception as e:
            print(f"Error deleting appointment: {e}")
            return 0
