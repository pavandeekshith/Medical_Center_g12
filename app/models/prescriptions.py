from app.utils.database import get_db_connection

class Prescription:
    def __init__(self, prescription_id=None, appointment_id=None, doctor_id=None, 
                 student_id=None, medication_id=None, prescription_date=None, 
                 quantity=None, instructions=None):
        self.prescription_id = prescription_id
        self.appointment_id = appointment_id
        self.doctor_id = doctor_id
        self.student_id = student_id
        self.medication_id = medication_id
        self.prescription_date = prescription_date
        self.quantity = quantity
        self.instructions = instructions
    
    @staticmethod
    def get_all():
        """Get all prescriptions"""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = """
            SELECT p.*, s.FirstName as StudentFirstName, s.LastName as StudentLastName,
                   d.Name as DoctorName, m.Name as MedicationName, m.DosageForm
            FROM Prescription p
            JOIN Students s ON p.StudentID = s.StudentID
            JOIN G12_Doctors d ON p.DoctorID = d.DoctorID
            JOIN Medications m ON p.MedicationID = m.MedicationID
            ORDER BY p.PrescriptionDate DESC
        """
        
        cursor.execute(query)
        prescriptions = cursor.fetchall()
        cursor.close()
        
        return prescriptions
    
    @staticmethod
    def get_by_id(prescription_id):
        """Get prescription by ID"""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = """
            SELECT p.*, s.FirstName as StudentFirstName, s.LastName as StudentLastName,
                   d.Name as DoctorName, m.Name as MedicationName, m.DosageForm
            FROM Prescription p
            JOIN Students s ON p.StudentID = s.StudentID
            JOIN cs432cims.G12_Doctors d ON p.DoctorID = d.DoctorID
            JOIN Medications m ON p.MedicationID = m.MedicationID
            WHERE p.PrescriptionID = %s
        """
        
        cursor.execute(query, (prescription_id,))
        prescription = cursor.fetchone()
        cursor.close()
        
        return prescription
    
    @staticmethod
    def get_by_student(student_id):
        """Get prescriptions for a specific student"""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = """
            SELECT p.*, d.Name as DoctorName, m.Name as MedicationName, 
                   m.DosageForm, mg.DateGiven, mg.QuantityGiven
            FROM Prescription p
            JOIN cs432cims.G12_Doctors d ON p.DoctorID = d.DoctorID
            JOIN Medications m ON p.MedicationID = m.MedicationID
            LEFT JOIN MedicinesGiven mg ON p.PrescriptionID = mg.PrescriptionID
            WHERE p.StudentID = %s
            ORDER BY p.PrescriptionDate DESC
        """
        
        cursor.execute(query, (student_id,))
        prescriptions = cursor.fetchall()
        cursor.close()
        
        return prescriptions
    
    @staticmethod
    def get_by_doctor(doctor_id):
        """Get prescriptions issued by a specific doctor"""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = """
            SELECT p.*, s.FirstName as StudentFirstName, s.LastName as StudentLastName,
                   m.Name as MedicationName, m.DosageForm
            FROM Prescription p
            JOIN Students s ON p.StudentID = s.StudentID
            JOIN Medications m ON p.MedicationID = m.MedicationID
            WHERE p.DoctorID = %s
            ORDER BY p.PrescriptionDate DESC
        """
        
        cursor.execute(query, (doctor_id,))
        prescriptions = cursor.fetchall()
        cursor.close()
        
        return prescriptions
    
    @staticmethod
    def get_unfulfilled():
        """Get prescriptions that haven't been fulfilled yet"""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = """
            SELECT p.*, s.FirstName as StudentFirstName, s.LastName as StudentLastName,
                   d.Name as DoctorName, m.Name as MedicationName, m.DosageForm
            FROM Prescription p
            JOIN Students s ON p.StudentID = s.StudentID
            JOIN G12_Doctors d ON p.DoctorID = d.DoctorID
            JOIN Medications m ON p.MedicationID = m.MedicationID
            LEFT JOIN MedicinesGiven mg ON p.PrescriptionID = mg.PrescriptionID
            WHERE mg.MedicineGivenID IS NULL
            ORDER BY p.PrescriptionDate
        """
        
        cursor.execute(query)
        prescriptions = cursor.fetchall()
        cursor.close()
        
        return prescriptions
    
    @staticmethod
    def create(appointment_id, doctor_id, student_id, medication_id, 
               prescription_date, quantity, instructions):
        """Create a new prescription"""
        db = get_db_connection()
        cursor = db.cursor()
        
        query = """
            INSERT INTO Prescription (
                AppointmentID, DoctorID, StudentID, MedicationID, 
                PrescriptionDate, Quantity, Instructions
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        cursor.execute(query, (
            appointment_id, doctor_id, student_id, medication_id,
            prescription_date, quantity, instructions
        ))
        
        db.commit()
        
        prescription_id = cursor.lastrowid
        cursor.close()
        
        return prescription_id
    
    @staticmethod
    def update(prescription_id, data):
        """Update a prescription"""
        db = get_db_connection()
        cursor = db.cursor()
        
        set_clause = ", ".join([f"{key} = %s" for key in data.keys()])
        query = f"UPDATE Prescription SET {set_clause} WHERE PrescriptionID = %s"
        
        values = list(data.values())
        values.append(prescription_id)
        
        cursor.execute(query, tuple(values))
        db.commit()
        
        affected_rows = cursor.rowcount
        cursor.close()
        
        return affected_rows
    
    @staticmethod
    def delete(prescription_id):
        """Delete a prescription"""
        db = get_db_connection()
        cursor = db.cursor()
        
        query = "DELETE FROM Prescription WHERE PrescriptionID = %s"
        
        cursor.execute(query, (prescription_id,))
        db.commit()
        
        affected_rows = cursor.rowcount
        cursor.close()
        
        return affected_rows

class MedicineGiven:
    def __init__(self, medicine_given_id=None, prescription_id=None, medication_id=None,
                 date_given=None, quantity_given=None):
        self.medicine_given_id = medicine_given_id
        self.prescription_id = prescription_id
        self.medication_id = medication_id
        self.date_given = date_given
        self.quantity_given = quantity_given
    
    @staticmethod
    def get_all():
        """Get all medicine given records"""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = """
            SELECT mg.*, m.Name as MedicationName, s.FirstName as StudentFirstName, 
                   s.LastName as StudentLastName
            FROM MedicinesGiven mg
            JOIN Prescription p ON mg.PrescriptionID = p.PrescriptionID
            JOIN Medications m ON mg.MedicationID = m.MedicationID
            JOIN Students s ON p.StudentID = s.StudentID
            ORDER BY mg.DateGiven DESC
        """
        
        cursor.execute(query)
        medicines_given = cursor.fetchall()
        cursor.close()
        
        return medicines_given
    
    @staticmethod
    def get_by_prescription(prescription_id):
        """Get medicine given records for a specific prescription"""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = """
            SELECT mg.*, m.Name as MedicationName
            FROM MedicinesGiven mg
            JOIN Medications m ON mg.MedicationID = m.MedicationID
            WHERE mg.PrescriptionID = %s
            ORDER BY mg.DateGiven DESC
        """
        
        cursor.execute(query, (prescription_id,))
        medicines_given = cursor.fetchall()
        cursor.close()
        
        return medicines_given
    
    @staticmethod
    def create(prescription_id, medication_id, date_given, quantity_given):
        """Create a new medicine given record"""
        db = get_db_connection()
        cursor = db.cursor()
        
        query = """
            INSERT INTO MedicinesGiven (
                PrescriptionID, MedicationID, DateGiven, QuantityGiven
            ) VALUES (%s, %s, %s, %s)
        """
        
        cursor.execute(query, (
            prescription_id, medication_id, date_given, quantity_given
        ))
        
        db.commit()
        
        # Update medication stock
        stock_query = """
            UPDATE Medications 
            SET QuantityInStock = QuantityInStock - %s 
            WHERE MedicationID = %s AND QuantityInStock >= %s
        """
        
        cursor.execute(stock_query, (quantity_given, medication_id, quantity_given))
        
        if cursor.rowcount == 0:
            # Roll back if not enough stock
            db.rollback()
            cursor.close()
            return -1
        
        db.commit()
        medicine_given_id = cursor.lastrowid
        cursor.close()
        
        return medicine_given_id
    
    @staticmethod
    def update(medicine_given_id, data):
        """Update a medicine given record"""
        db = get_db_connection()
        cursor = db.cursor()
        
        # First get the current record to calculate stock adjustment
        query = "SELECT * FROM MedicinesGiven WHERE MedicineGivenID = %s"
        cursor.execute(query, (medicine_given_id,))
        current = cursor.fetchone()
        
        if not current:
            cursor.close()
            return 0
        
        # Calculate stock adjustment if quantity is being updated
        if 'QuantityGiven' in data:
            old_quantity = current['QuantityGiven']
            new_quantity = data['QuantityGiven']
            quantity_diff = old_quantity - new_quantity
            
            # Update medication stock
            stock_query = """
                UPDATE Medications 
                SET QuantityInStock = QuantityInStock + %s 
                WHERE MedicationID = %s AND (QuantityInStock + %s >= 0 OR %s > 0)
            """
            
            cursor.execute(stock_query, (
                quantity_diff, 
                data.get('MedicationID', current['MedicationID']),
                quantity_diff,
                quantity_diff
            ))
            
            if cursor.rowcount == 0 and quantity_diff < 0:
                # Roll back if not enough stock
                cursor.close()
                return 0
        
        # Update the medicine given record
        set_clause = ", ".join([f"{key} = %s" for key in data.keys()])
        update_query = f"UPDATE MedicinesGiven SET {set_clause} WHERE MedicineGivenID = %s"
        
        values = list(data.values())
        values.append(medicine_given_id)
        
        cursor.execute(update_query, tuple(values))
        db.commit()
        
        affected_rows = cursor.rowcount
        cursor.close()
        
        return affected_rows
    
    @staticmethod
    def delete(medicine_given_id):
        """Delete a medicine given record"""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # First get the current record to adjust stock
        query = "SELECT * FROM MedicinesGiven WHERE MedicineGivenID = %s"
        cursor.execute(query, (medicine_given_id,))
        record = cursor.fetchone()
        
        if not record:
            cursor.close()
            return 0
        
        # Update medication stock (add back the quantity)
        stock_query = """
            UPDATE Medications 
            SET QuantityInStock = QuantityInStock + %s 
            WHERE MedicationID = %s
        """
        
        cursor.execute(stock_query, (record['QuantityGiven'], record['MedicationID']))
        
        # Delete the record
        delete_query = "DELETE FROM MedicinesGiven WHERE MedicineGivenID = %s"
        cursor.execute(delete_query, (medicine_given_id,))
        
        db.commit()
        affected_rows = cursor.rowcount
        cursor.close()
        
        return affected_rows
