from app.utils.database import get_db_connection

class Student:
    def __init__(self, student_id=None, first_name=None, last_name=None, 
                 gender=None, date_of_birth=None, email=None, 
                 contact_number=None, address=None):
        self.student_id = student_id
        self.first_name = first_name
        self.last_name = last_name
        self.gender = gender
        self.date_of_birth = date_of_birth
        self.email = email
        self.contact_number = contact_number
        self.address = address
    
    @staticmethod
    def get_all():
        """Get all students"""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = "SELECT * FROM Students ORDER BY FirstName, LastName"
        
        cursor.execute(query)
        students = cursor.fetchall()
        cursor.close()
        
        return students
    
    @staticmethod
    def get_by_id(student_id):
        """Get student by ID"""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = "SELECT * FROM Students WHERE StudentID = %s"
        
        cursor.execute(query, (student_id,))
        student = cursor.fetchone()
        cursor.close()
        
        return student
    
    @staticmethod
    def search(term):
        """Search students by name or ID"""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = """
            SELECT * FROM Students 
            WHERE StudentID LIKE %s OR FirstName LIKE %s OR LastName LIKE %s
            ORDER BY FirstName, LastName
        """
        
        term = f'%{term}%'
        cursor.execute(query, (term, term, term))
        students = cursor.fetchall()
        cursor.close()
        
        return students
    
    @staticmethod
    def create(first_name, last_name, gender, date_of_birth=None, 
               email=None, contact_number=None, address=None):
        """Create a new student"""
        db = get_db_connection()
        cursor = db.cursor()
        
        query = """
            INSERT INTO Students (
                FirstName, LastName, Gender, DateOfBirth, Email, ContactNumber, Address
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        cursor.execute(query, (
            first_name, last_name, gender, date_of_birth, 
            email, contact_number, address
        ))
        
        db.commit()
        
        student_id = cursor.lastrowid
        cursor.close()
        
        return student_id
    
    @staticmethod
    def update(student_id, data):
        """Update a student"""
        db = get_db_connection()
        cursor = db.cursor()
        
        set_clause = ", ".join([f"{key} = %s" for key in data.keys()])
        query = f"UPDATE Students SET {set_clause} WHERE StudentID = %s"
        
        values = list(data.values())
        values.append(student_id)
        
        cursor.execute(query, tuple(values))
        db.commit()
        
        affected_rows = cursor.rowcount
        cursor.close()
        
        return affected_rows
    
    @staticmethod
    def delete(student_id):
        """Delete a student"""
        db = get_db_connection()
        cursor = db.cursor()
        
        query = "DELETE FROM Students WHERE StudentID = %s"
        
        cursor.execute(query, (student_id,))
        db.commit()
        
        affected_rows = cursor.rowcount
        cursor.close()
        
        return affected_rows
    
    @staticmethod
    def get_medical_history(student_id):
        """Get medical history for a student"""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = """
            SELECT 
                a.AppointmentDate, a.AppointmentTime, 
                d.Name as DoctorName, d.Specialization,
                p.PrescriptionID, p.Instructions,
                m.Name as MedicationName, m.DosageForm,
                p.Quantity as PrescribedQuantity,
                mg.DateGiven, mg.QuantityGiven
            FROM Appointments a
            LEFT JOIN G12_Doctors d ON a.DoctorID = d.DoctorID
            LEFT JOIN Prescription p ON a.AppointmentID = p.AppointmentID
            LEFT JOIN Medications m ON p.MedicationID = m.MedicationID
            LEFT JOIN MedicinesGiven mg ON p.PrescriptionID = mg.PrescriptionID
            WHERE a.StudentID = %s
            ORDER BY a.AppointmentDate DESC, a.AppointmentTime DESC
        """
        
        cursor.execute(query, (student_id,))
        history = cursor.fetchall()
        cursor.close()
        
        return history
