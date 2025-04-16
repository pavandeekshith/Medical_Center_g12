"""
CRUD Operations for CIMS Database

This module provides functions for Create, Read, Update and Delete operations
on tables in the cs432g12 database and G12_Doctors table in cs432cims database.
"""

import mysql.connector
from mysql.connector import Error
import logging
import sqlite3

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='cims_crud.log'
)
logger = logging.getLogger('cims_crud')

# Database configurations
DB_CONFIGS = {
    "cims": {
        "host": "10.0.116.125",
        "user": "cs432g12",
        "password": "T7XnJqYz",
        "database": "cs432cims"
    },
    "g12": {
        "host": "10.0.116.125",
        "user": "cs432g12",
        "password": "T7XnJqYz",
        "database": "cs432g12"
    }
}

def get_db_connection(db_name="g12"):
    """
    Create and return a database connection
    
    Args:
        db_name (str): The database to connect to ("cims" or "g12")
        
    Returns:
        mysql.connector.connection: Database connection object
        
    Raises:
        ValueError: If db_name is not valid
        ConnectionError: If connection fails
    """
    if db_name not in DB_CONFIGS:
        raise ValueError(f"Invalid database name: {db_name}. Valid options are 'cims' or 'g12'")
    
    try:
        connection = mysql.connector.connect(**DB_CONFIGS[db_name])
        return connection
    except Error as e:
        logger.error(f"Error connecting to MySQL database: {e}")
        raise ConnectionError(f"Failed to connect to database: {e}")

# Add function to get members from the SQLite database
def get_members():
    """
    Retrieve all members from the SQLite database
    
    Returns:
        list: List of member records
    """
    try:
        conn = sqlite3.connect('cims.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM members")
        members = [dict(row) for row in cursor.fetchall()]
        
        return members
    except sqlite3.Error as e:
        logger.error(f"Error fetching members from SQLite database: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()

# Generic CRUD Operations

def execute_query(query, params=None, db_name="g12", fetch=False):
    """
    Execute a SQL query with optional parameters
    
    Args:
        query (str): SQL query to execute
        params (tuple, list, dict, optional): Parameters for the query
        db_name (str): Database to use ("cims" or "g12")
        fetch (bool): Whether to fetch results
        
    Returns:
        list or int: Query results if fetch=True, or affected row count if fetch=False
        
    Raises:
        Exception: If query execution fails
    """
    connection = None
    cursor = None
    try:
        connection = get_db_connection(db_name)
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute(query, params)
        
        if fetch:
            results = cursor.fetchall()
            return results
        else:
            connection.commit()
            return cursor.rowcount
            
    except Error as e:
        if connection:
            connection.rollback()
        logger.error(f"Error executing query: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

# Generic CRUD functions

def create_record(table, data, db_name="g12"):
    """
    Insert a new record into a table
    
    Args:
        table (str): Table name
        data (dict): Column-value pairs to insert
        db_name (str): Database to use
        
    Returns:
        int: ID of the inserted record, or -1 if insert failed
    """
    try:
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        values = tuple(data.values())
        
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        connection = get_db_connection(db_name)
        cursor = connection.cursor()
        
        cursor.execute(query, values)
        connection.commit()
        
        last_id = cursor.lastrowid
        logger.info(f"Created record in {table} with ID {last_id}")
        
        return last_id
        
    except Error as e:
        logger.error(f"Error creating record in {table}: {e}")
        return -1
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def read_records(table, columns="*", where=None, params=None, db_name="g12", limit=None, order_by=None):
    """
    Read records from a table
    
    Args:
        table (str): Table name
        columns (str): Columns to select (default "*")
        where (str, optional): WHERE clause
        params (tuple, optional): Parameters for WHERE clause
        db_name (str): Database to use
        limit (int, optional): Limit number of records
        order_by (str, optional): ORDER BY clause
        
    Returns:
        list: List of records as dictionaries
    """
    try:
        query = f"SELECT {columns} FROM {table}"
        
        if where:
            query += f" WHERE {where}"
            
        if order_by:
            query += f" ORDER BY {order_by}"
            
        if limit:
            query += f" LIMIT {limit}"
            
        records = execute_query(query, params, db_name, fetch=True)
        return records
        
    except Error as e:
        logger.error(f"Error reading records from {table}: {e}")
        return []

def update_record(table, data, where_clause, where_params, db_name="g12"):
    """
    Update records in a table
    
    Args:
        table (str): Table name
        data (dict): Column-value pairs to update
        where_clause (str): WHERE clause
        where_params (tuple): Parameters for WHERE clause
        db_name (str): Database to use
        
    Returns:
        int: Number of affected rows
    """
    try:
        set_clause = ", ".join([f"{column} = %s" for column in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        
        # Combine data values and where_params
        params = tuple(data.values()) + where_params
        
        connection = get_db_connection(db_name)
        cursor = connection.cursor()
        
        cursor.execute(query, params)
        connection.commit()
        
        affected_rows = cursor.rowcount
        logger.info(f"Updated {affected_rows} records in {table}")
        
        return affected_rows
        
    except Error as e:
        logger.error(f"Error updating records in {table}: {e}")
        return 0
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def delete_record(table, where_clause, where_params, db_name="g12"):
    """
    Delete records from a table
    
    Args:
        table (str): Table name
        where_clause (str): WHERE clause
        where_params (tuple): Parameters for WHERE clause
        db_name (str): Database to use
        
    Returns:
        int: Number of deleted rows
    """
    try:
        query = f"DELETE FROM {table} WHERE {where_clause}"
        
        connection = get_db_connection(db_name)
        cursor = connection.cursor()
        
        cursor.execute(query, where_params)
        connection.commit()
        
        affected_rows = cursor.rowcount
        logger.info(f"Deleted {affected_rows} records from {table}")
        
        return affected_rows
        
    except Error as e:
        logger.error(f"Error deleting records from {table}: {e}")
        return 0
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

# Specific table operations

# G12_Doctors operations (in cims database)
def create_doctor(name, specialization, email, contact_number, image=None):
    """
    Create a new doctor record
    
    Args:
        name (str): Doctor's name
        specialization (str): Doctor's specialization
        email (str): Doctor's email
        contact_number (str): Doctor's contact number
        image (bytes, optional): Doctor's image
        
    Returns:
        int: Doctor ID if successful, -1 otherwise
    """
    data = {
        "Name": name,
        "Specialization": specialization,
        "Email": email,
        "ContactNumber": contact_number
    }
    
    if image is not None:
        data["Image"] = image
        
    return create_record("G12_Doctors", data, "cims")

def get_doctors(where=None, params=None):
    """
    Get doctor records with optional filtering
    
    Args:
        where (str, optional): WHERE clause
        params (tuple, optional): Parameters for WHERE clause
        
    Returns:
        list: List of doctor records
    """
    return read_records("G12_Doctors", where=where, params=params, db_name="cims")

def update_doctor(doctor_id, data):
    """
    Update a doctor record
    
    Args:
        doctor_id (int): Doctor ID to update
        data (dict): Column-value pairs to update
        
    Returns:
        int: Number of affected rows
    """
    return update_record("G12_Doctors", data, "DoctorID = %s", (doctor_id,), "cims")

def delete_doctor(doctor_id):
    """
    Delete a doctor record
    
    Args:
        doctor_id (int): Doctor ID to delete
        
    Returns:
        int: 1 if successful, 0 otherwise
    """
    return delete_record("G12_Doctors", "DoctorID = %s", (doctor_id,), "cims")

# Appointments operations
def create_appointment(student_id, doctor_id, appointment_date, appointment_time, status):
    """
    Create a new appointment record
    
    Args:
        student_id (int): Student ID
        doctor_id (int): Doctor ID  
        appointment_date (str): Date in YYYY-MM-DD format
        appointment_time (str): Time in HH:MM format
        status (str): Appointment status
        
    Returns:
        int: Appointment ID if successful, -1 otherwise
    """
    data = {
        "StudentID": student_id,
        "DoctorID": doctor_id,
        "AppointmentDate": appointment_date,
        "AppointmentTime": appointment_time,
        "Status": status
    }
    return create_record("Appointments", data)

def get_appointments(where=None, params=None):
    """
    Get appointment records with optional filtering
    
    Args:
        where (str, optional): WHERE clause
        params (tuple, optional): Parameters for WHERE clause
        
    Returns:
        list: List of appointment records
    """
    return read_records("Appointments", where=where, params=params)

def update_appointment(appointment_id, data):
    """
    Update an appointment record
    
    Args:
        appointment_id (int): Appointment ID to update
        data (dict): Column-value pairs to update
        
    Returns:
        int: Number of affected rows
    """
    return update_record("Appointments", data, "AppointmentID = %s", (appointment_id,))

def delete_appointment(appointment_id):
    """
    Delete an appointment record
    
    Args:
        appointment_id (int): Appointment ID to delete
        
    Returns:
        int: 1 if successful, 0 otherwise
    """
    return delete_record("Appointments", "AppointmentID = %s", (appointment_id,))

# DoctorAvailability operations
def create_doctor_availability(doctor_id, availability_date, start_time, end_time, status):
    """
    Create a new doctor availability record
    
    Args:
        doctor_id (int): Doctor ID
        availability_date (str): Date in YYYY-MM-DD format
        start_time (str): Start time in HH:MM format
        end_time (str): End time in HH:MM format
        status (str): Availability status
        
    Returns:
        int: Availability ID if successful, -1 otherwise
    """
    data = {
        "DoctorID": doctor_id,
        "AvailabilityDate": availability_date,
        "StartTime": start_time,
        "EndTime": end_time,
        "Status": status
    }
    return create_record("DoctorAvailability", data)

def get_doctor_availability(where=None, params=None):
    """
    Get doctor availability records with optional filtering
    
    Args:
        where (str, optional): WHERE clause
        params (tuple, optional): Parameters for WHERE clause
        
    Returns:
        list: List of doctor availability records
    """
    return read_records("DoctorAvailability", where=where, params=params)

def update_doctor_availability(availability_id, data):
    """
    Update a doctor availability record
    
    Args:
        availability_id (int): Availability ID to update
        data (dict): Column-value pairs to update
        
    Returns:
        int: Number of affected rows
    """
    return update_record("DoctorAvailability", data, "AvailabilityID = %s", (availability_id,))

def delete_doctor_availability(availability_id):
    """
    Delete a doctor availability record
    
    Args:
        availability_id (int): Availability ID to delete
        
    Returns:
        int: 1 if successful, 0 otherwise
    """
    return delete_record("DoctorAvailability", "AvailabilityID = %s", (availability_id,))

# EmergencyCases operations
def create_emergency_case(student_id, case_date, case_time, description, severity, handled_by_staff_id=None, vehicle_id=None):
    """
    Create a new emergency case record
    
    Args:
        student_id (int): Student ID
        case_date (str): Date in YYYY-MM-DD format
        case_time (str): Time in HH:MM format
        description (str): Case description
        severity (str): Case severity
        handled_by_staff_id (int, optional): Staff ID who handled the case
        vehicle_id (int, optional): Vehicle ID used for the emergency
        
    Returns:
        int: Case ID if successful, -1 otherwise
    """
    data = {
        "StudentID": student_id,
        "CaseDate": case_date,
        "CaseTime": case_time,
        "Description": description,
        "Severity": severity
    }
    
    if handled_by_staff_id is not None:
        data["HandledByStaffID"] = handled_by_staff_id
        
    if vehicle_id is not None:
        data["VehicleID"] = vehicle_id
        
    return create_record("EmergencyCases", data)

def get_emergency_cases(where=None, params=None):
    """
    Get emergency case records with optional filtering
    
    Args:
        where (str, optional): WHERE clause
        params (tuple, optional): Parameters for WHERE clause
        
    Returns:
        list: List of emergency case records
    """
    return read_records("EmergencyCases", where=where, params=params)

def update_emergency_case(case_id, data):
    """
    Update an emergency case record
    
    Args:
        case_id (int): Case ID to update
        data (dict): Column-value pairs to update
        
    Returns:
        int: Number of affected rows
    """
    return update_record("EmergencyCases", data, "CaseID = %s", (case_id,))

def delete_emergency_case(case_id):
    """
    Delete an emergency case record
    
    Args:
        case_id (int): Case ID to delete
        
    Returns:
        int: 1 if successful, 0 otherwise
    """
    return delete_record("EmergencyCases", "CaseID = %s", (case_id,))

# HospitalReferrals operations
def create_hospital_referral(student_id, referral_date, hospital_name, reason, referred_by_doctor_id):
    """
    Create a new hospital referral record
    
    Args:
        student_id (int): Student ID
        referral_date (str): Date in YYYY-MM-DD format
        hospital_name (str): Hospital name
        reason (str): Referral reason
        referred_by_doctor_id (int): Doctor ID who made the referral
        
    Returns:
        int: Referral ID if successful, -1 otherwise
    """
    data = {
        "StudentID": student_id,
        "ReferralDate": referral_date,
        "HospitalName": hospital_name,
        "Reason": reason,
        "ReferredByDoctorID": referred_by_doctor_id
    }
    return create_record("HospitalReferrals", data)

def get_hospital_referrals(where=None, params=None):
    """
    Get hospital referral records with optional filtering
    
    Args:
        where (str, optional): WHERE clause
        params (tuple, optional): Parameters for WHERE clause
        
    Returns:
        list: List of hospital referral records
    """
    return read_records("HospitalReferrals", where=where, params=params)

def update_hospital_referral(referral_id, data):
    """
    Update a hospital referral record
    
    Args:
        referral_id (int): Referral ID to update
        data (dict): Column-value pairs to update
        
    Returns:
        int: Number of affected rows
    """
    return update_record("HospitalReferrals", data, "ReferralID = %s", (referral_id,))

def delete_hospital_referral(referral_id):
    """
    Delete a hospital referral record
    
    Args:
        referral_id (int): Referral ID to delete
        
    Returns:
        int: 1 if successful, 0 otherwise
    """
    return delete_record("HospitalReferrals", "ReferralID = %s", (referral_id,))

# Medications operations
def create_medication(name, dosage_form, quantity_in_stock, expiry_date=None):
    """
    Create a new medication record
    
    Args:
        name (str): Medication name
        dosage_form (str): Dosage form (e.g., tablet, syrup)
        quantity_in_stock (int): Quantity in stock
        expiry_date (str, optional): Expiry date in YYYY-MM-DD format
        
    Returns:
        int: Medication ID if successful, -1 otherwise
    """
    data = {
        "Name": name,
        "DosageForm": dosage_form,
        "QuantityInStock": quantity_in_stock
    }
    
    if expiry_date is not None:
        data["ExpiryDate"] = expiry_date
        
    return create_record("Medications", data)

def get_medications(where=None, params=None):
    """
    Get medication records with optional filtering
    
    Args:
        where (str, optional): WHERE clause
        params (tuple, optional): Parameters for WHERE clause
        
    Returns:
        list: List of medication records
    """
    return read_records("Medications", where=where, params=params)

def update_medication(medication_id, data):
    """
    Update a medication record
    
    Args:
        medication_id (int): Medication ID to update
        data (dict): Column-value pairs to update
        
    Returns:
        int: Number of affected rows
    """
    return update_record("Medications", data, "MedicationID = %s", (medication_id,))

def delete_medication(medication_id):
    """
    Delete a medication record
    
    Args:
        medication_id (int): Medication ID to delete
        
    Returns:
        int: 1 if successful, 0 otherwise
    """
    return delete_record("Medications", "MedicationID = %s", (medication_id,))

# MedicinesGiven operations
def create_medicine_given(student_id, medication_id, given_date, given_time, quantity, given_by_staff_id):
    """
    Create a new medicine given record
    
    Args:
        student_id (int): Student ID
        medication_id (int): Medication ID
        given_date (str): Date in YYYY-MM-DD format
        given_time (str): Time in HH:MM format
        quantity (int): Quantity given
        given_by_staff_id (int): Staff ID who gave the medicine
        
    Returns:
        int: Record ID if successful, -1 otherwise
    """
    data = {
        "StudentID": student_id,
        "MedicationID": medication_id,
        "GivenDate": given_date,
        "GivenTime": given_time,
        "Quantity": quantity,
        "GivenByStaffID": given_by_staff_id
    }
    return create_record("MedicinesGiven", data)

def get_medicines_given(where=None, params=None):
    """
    Get medicines given records with optional filtering
    
    Args:
        where (str, optional): WHERE clause
        params (tuple, optional): Parameters for WHERE clause
        
    Returns:
        list: List of medicines given records
    """
    return read_records("MedicinesGiven", where=where, params=params)

def update_medicine_given(record_id, data):
    """
    Update a medicine given record
    
    Args:
        record_id (int): Record ID to update
        data (dict): Column-value pairs to update
        
    Returns:
        int: Number of affected rows
    """
    return update_record("MedicinesGiven", data, "RecordID = %s", (record_id,))

def delete_medicine_given(record_id):
    """
    Delete a medicine given record
    
    Args:
        record_id (int): Record ID to delete
        
    Returns:
        int: 1 if successful, 0 otherwise
    """
    return delete_record("MedicinesGiven", "RecordID = %s", (record_id,))

# Prescription operations
def create_prescription(appointment_id, doctor_id, student_id, medication_id, prescription_date, quantity, instructions):
    """
    Create a new prescription record
    
    Args:
        appointment_id (int): Appointment ID
        doctor_id (int): Doctor ID
        student_id (int): Student ID
        medication_id (int): Medication ID
        prescription_date (str): Date in YYYY-MM-DD format
        quantity (int): Quantity prescribed
        instructions (str): Usage instructions
        
    Returns:
        int: Prescription ID if successful, -1 otherwise
    """
    data = {
        "AppointmentID": appointment_id,
        "DoctorID": doctor_id,
        "StudentID": student_id,
        "MedicationID": medication_id,
        "PrescriptionDate": prescription_date,
        "Quantity": quantity,
        "Instructions": instructions
    }
    return create_record("Prescription", data)

def get_prescriptions(where=None, params=None):
    """
    Get prescription records with optional filtering
    
    Args:
        where (str, optional): WHERE clause
        params (tuple, optional): Parameters for WHERE clause
        
    Returns:
        list: List of prescription records
    """
    return read_records("Prescription", where=where, params=params)

def update_prescription(prescription_id, data):
    """
    Update a prescription record
    
    Args:
        prescription_id (int): Prescription ID to update
        data (dict): Column-value pairs to update
        
    Returns:
        int: Number of affected rows
    """
    return update_record("Prescription", data, "PrescriptionID = %s", (prescription_id,))

def delete_prescription(prescription_id):
    """
    Delete a prescription record
    
    Args:
        prescription_id (int): Prescription ID to delete
        
    Returns:
        int: 1 if successful, 0 otherwise
    """
    return delete_record("Prescription", "PrescriptionID = %s", (prescription_id,))

# Staff operations
def create_staff(first_name, last_name, role, email=None, contact_number=None):
    """
    Create a new staff record
    
    Args:
        first_name (str): Staff first name
        last_name (str): Staff last name
        role (str): Staff role
        email (str, optional): Staff email
        contact_number (str, optional): Staff contact number
        
    Returns:
        int: Staff ID if successful, -1 otherwise
    """
    data = {
        "FirstName": first_name,
        "LastName": last_name,
        "Role": role
    }
    
    if email is not None:
        data["Email"] = email
        
    if contact_number is not None:
        data["ContactNumber"] = contact_number
        
    return create_record("Staff", data)

def get_staff(where=None, params=None):
    """
    Get staff records with optional filtering
    
    Args:
        where (str, optional): WHERE clause
        params (tuple, optional): Parameters for WHERE clause
        
    Returns:
        list: List of staff records
    """
    return read_records("Staff", where=where, params=params)

def update_staff(staff_id, data):
    """
    Update a staff record
    
    Args:
        staff_id (int): Staff ID to update
        data (dict): Column-value pairs to update
        
    Returns:
        int: Number of affected rows
    """
    return update_record("Staff", data, "StaffID = %s", (staff_id,))

def delete_staff(staff_id):
    """
    Delete a staff record
    
    Args:
        staff_id (int): Staff ID to delete
        
    Returns:
        int: 1 if successful, 0 otherwise
    """
    return delete_record("Staff", "StaffID = %s", (staff_id,))

# Students operations
def create_student(first_name, last_name, gender, dob=None, email=None, address=None, contact_number=None):
    """
    Create a new student record
    
    Args:
        first_name (str): Student first name
        last_name (str): Student last name
        gender (str): Student gender
        dob (str, optional): Date of birth in YYYY-MM-DD format
        email (str, optional): Student email
        address (str, optional): Student address
        contact_number (str, optional): Student contact number
        
    Returns:
        int: Student ID if successful, -1 otherwise
    """
    data = {
        "FirstName": first_name,
        "LastName": last_name,
        "Gender": gender
    }
    
    if dob is not None:
        data["DateOfBirth"] = dob
        
    if email is not None:
        data["Email"] = email
        
    if address is not None:
        data["Address"] = address
        
    if contact_number is not None:
        data["ContactNumber"] = contact_number
        
    return create_record("Students", data)

def get_students(where=None, params=None):
    """
    Get student records with optional filtering
    
    Args:
        where (str, optional): WHERE clause
        params (tuple, optional): Parameters for WHERE clause
        
    Returns:
        list: List of student records
    """
    return read_records("Students", where=where, params=params)

def update_student(student_id, data):
    """
    Update a student record
    
    Args:
        student_id (int): Student ID to update
        data (dict): Column-value pairs to update
        
    Returns:
        int: Number of affected rows
    """
    return update_record("Students", data, "StudentID = %s", (student_id,))

def delete_student(student_id):
    """
    Delete a student record
    
    Args:
        student_id (int): Student ID to delete
        
    Returns:
        int: 1 if successful, 0 otherwise
    """
    return delete_record("Students", "StudentID = %s", (student_id,))

# Vehicles operations
def create_vehicle(vehicle_type, driver_staff_id=None, availability_status=None):
    """
    Create a new vehicle record
    
    Args:
        vehicle_type (str): Vehicle type
        driver_staff_id (int, optional): Staff ID who drives the vehicle
        availability_status (str, optional): Vehicle availability status
        
    Returns:
        int: Vehicle ID if successful, -1 otherwise
    """
    data = {
        "VehicleType": vehicle_type
    }
    
    if driver_staff_id is not None:
        data["DriverStaffID"] = driver_staff_id
        
    if availability_status is not None:
        data["AvailabilityStatus"] = availability_status
        
    return create_record("Vehicles", data)

def get_vehicles(where=None, params=None):
    """
    Get vehicle records with optional filtering
    
    Args:
        where (str, optional): WHERE clause
        params (tuple, optional): Parameters for WHERE clause
        
    Returns:
        list: List of vehicle records
    """
    return read_records("Vehicles", where=where, params=params)

def update_vehicle(vehicle_id, data):
    """
    Update a vehicle record
    
    Args:
        vehicle_id (int): Vehicle ID to update
        data (dict): Column-value pairs to update
        
    Returns:
        int: Number of affected rows
    """
    return update_record("Vehicles", data, "VehicleID = %s", (vehicle_id,))

def delete_vehicle(vehicle_id):
    """
    Delete a vehicle record
    
    Args:
        vehicle_id (int): Vehicle ID to delete
        
    Returns:
        int: 1 if successful, 0 otherwise
    """
    return delete_record("Vehicles", "VehicleID = %s", (vehicle_id,))