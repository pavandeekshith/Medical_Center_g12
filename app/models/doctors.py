from app.utils.database import get_db_connection
from datetime import datetime, timedelta

class Doctor:
    def __init__(self, doctor_id=None, name=None, specialization=None, 
                 email=None, contact_number=None, image=None):
        self.doctor_id = doctor_id
        self.name = name
        self.specialization = specialization
        self.email = email
        self.contact_number = contact_number
        self.image = image
    
    @staticmethod
    def get_all():
        """Get all doctors"""
        db = get_db_connection('cims')
        cursor = db.cursor(dictionary=True)
        
        query = "SELECT * FROM G12_Doctors"
        
        cursor.execute(query)
        doctors = cursor.fetchall()
        cursor.close()
        
        return doctors
    
    @staticmethod
    def get_by_id(doctor_id):
        """Get doctor details by ID."""
        conn = get_db_connection('cims')
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM Doctors WHERE DoctorID = %s', (doctor_id,))
        
        doctor = cursor.fetchone()
        conn.close()
        
        return doctor
    
    @staticmethod
    def create(name, specialization, email, contact_number, image=None):
        """Create a new doctor"""
        db = get_db_connection('cims')
        cursor = db.cursor()
        
        if image:
            query = """
                INSERT INTO G12_Doctors (Name, Specialization, Email, ContactNumber, Image)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (name, specialization, email, contact_number, image))
        else:
            query = """
                INSERT INTO G12_Doctors (Name, Specialization, Email, ContactNumber)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (name, specialization, email, contact_number))
        
        db.commit()
        
        doctor_id = cursor.lastrowid
        cursor.close()
        
        return doctor_id
    
    @staticmethod
    def update(doctor_id, data):
        """Update a doctor"""
        db = get_db_connection('cims')
        cursor = db.cursor()
        
        set_clause = ", ".join([f"{key} = %s" for key in data.keys()])
        query = f"UPDATE G12_Doctors SET {set_clause} WHERE DoctorID = %s"
        
        values = list(data.values())
        values.append(doctor_id)
        
        cursor.execute(query, tuple(values))
        db.commit()
        
        affected_rows = cursor.rowcount
        cursor.close()
        
        return affected_rows
    
    @staticmethod
    def delete(doctor_id):
        """Delete a doctor"""
        db = get_db_connection('cims')
        cursor = db.cursor()
        
        query = "DELETE FROM G12_Doctors WHERE DoctorID = %s"
        
        cursor.execute(query, (doctor_id,))
        db.commit()
        
        affected_rows = cursor.rowcount
        cursor.close()
        
        return affected_rows

class DoctorAvailability:
    def __init__(self, availability_id=None, doctor_id=None, availability_date=None,
                 start_time=None, end_time=None, status=None):
        self.availability_id = availability_id
        self.doctor_id = doctor_id
        self.availability_date = availability_date
        self.start_time = start_time
        self.end_time = end_time
        self.status = status
    
    @staticmethod
    def get_all():
        """Get all doctor availability records"""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = """
            SELECT da.*, d.Name as DoctorName
            FROM DoctorAvailability da
            JOIN cs432cims.G12_Doctors d ON da.DoctorID = d.DoctorID
        """
        
        cursor.execute(query)
        availabilities = cursor.fetchall()
        cursor.close()
        
        return availabilities
    
    @staticmethod
    def get_by_doctor(doctor_id):
        """Get doctor availability by doctor ID."""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)  # Use dictionary cursor to return dictionaries
        
        # Get the doctor's working hours
        cursor.execute(
            'SELECT * FROM DoctorAvailability WHERE DoctorID = %s',
            (doctor_id,)
        )
        
        availability = cursor.fetchall()
        conn.close()
        
        return availability
    
    @staticmethod
    def get_available_slots(doctor_id, date):
        """Get available appointment slots for a doctor on a specific date."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Format date to match database format
        try:
            # Parse input date to ensure correct format
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%Y-%m-%d')
            
            # Get day of week (0 = Monday, 6 = Sunday)
            day_of_week = date_obj.weekday()
            weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            day_name = weekdays[day_of_week]
            
            # Check if the doctor works on this day
            cursor.execute(
                'SELECT * FROM DoctorAvailability WHERE DoctorID = %s AND DayOfWeek = %s',
                (doctor_id, day_name)
            )
            
            doctor_schedule = cursor.fetchall()
            if not doctor_schedule:
                return []
                
            # Get all booked appointments for this doctor on this date
            cursor.execute(
                'SELECT AppointmentTime FROM Appointments WHERE DoctorID = %s AND AppointmentDate = %s AND Status != "Cancelled"',
                (doctor_id, formatted_date)
            )
            
            booked_slots = [row['AppointmentTime'] for row in cursor.fetchall()]
            
            # Generate all possible slots based on doctor's schedule
            all_slots = []
            for schedule in doctor_schedule:
                start_time = datetime.strptime(schedule['StartTime'], '%H:%M:%S')
                end_time = datetime.strptime(schedule['EndTime'], '%H:%M:%S')
                
                # Generate slots every 15 minutes
                current_slot = start_time
                while current_slot < end_time:
                    slot_time = current_slot.strftime('%H:%M:%S')
                    
                    # Check if this slot is booked
                    status = 'Booked' if slot_time in booked_slots else 'Available'
                    
                    # Check if this slot is in the past (for today's slots)
                    if formatted_date == datetime.now().strftime('%Y-%m-%d'):
                        current_time = datetime.now()
                        if current_slot <= current_time:
                            status = 'Unavailable'
                    
                    all_slots.append({
                        'time': slot_time,
                        'status': status
                    })
                    
                    # Move to next slot (15 minutes later)
                    current_slot += timedelta(minutes=15)
            
            conn.close()
            return all_slots
            
        except Exception as e:
            print(f"Error getting available slots: {e}")
            conn.close()
            return []
    
    @staticmethod
    def create(doctor_id, availability_date, start_time, end_time, status='Available'):
        """Create a new doctor availability record"""
        db = get_db_connection()
        cursor = db.cursor()
        
        query = """
            INSERT INTO DoctorAvailability (DoctorID, AvailabilityDate, StartTime, EndTime, Status)
            VALUES (%s, %s, %s, %s, %s)
        """
        
        cursor.execute(query, (doctor_id, availability_date, start_time, end_time, status))
        db.commit()
        
        availability_id = cursor.lastrowid
        cursor.close()
        
        return availability_id
    
    @staticmethod
    def update(availability_id, data):
        """Update a doctor availability record"""
        db = get_db_connection()
        cursor = db.cursor()
        
        set_clause = ", ".join([f"{key} = %s" for key in data.keys()])
        query = f"UPDATE DoctorAvailability SET {set_clause} WHERE AvailabilityID = %s"
        
        values = list(data.values())
        values.append(availability_id)
        
        cursor.execute(query, tuple(values))
        db.commit()
        
        affected_rows = cursor.rowcount
        cursor.close()
        
        return affected_rows
    
    @staticmethod
    def delete(availability_id):
        """Delete a doctor availability record"""
        db = get_db_connection()
        cursor = db.cursor()
        
        query = "DELETE FROM DoctorAvailability WHERE AvailabilityID = %s"
        
        cursor.execute(query, (availability_id,))
        db.commit()
        
        affected_rows = cursor.rowcount
        cursor.close()
        
        return affected_rows
