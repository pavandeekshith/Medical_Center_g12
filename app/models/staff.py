from app.utils.database import get_db_connection

class Staff:
    def __init__(self, staff_id=None, first_name=None, last_name=None, 
                 role=None, email=None, contact_number=None):
        self.staff_id = staff_id
        self.first_name = first_name
        self.last_name = last_name
        self.role = role
        self.email = email
        self.contact_number = contact_number
    
    @staticmethod
    def get_all():
        """Get all staff members"""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = "SELECT * FROM Staff ORDER BY FirstName, LastName"
        
        cursor.execute(query)
        staff = cursor.fetchall()
        cursor.close()
        
        return staff
    
    @staticmethod
    def get_by_id(staff_id):
        """Get staff member by ID"""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = "SELECT * FROM Staff WHERE StaffID = %s"
        
        cursor.execute(query, (staff_id,))
        staff = cursor.fetchone()
        cursor.close()
        
        return staff
    
    @staticmethod
    def get_by_role(role):
        """Get staff members by role"""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = "SELECT * FROM Staff WHERE Role = %s ORDER BY FirstName, LastName"
        
        cursor.execute(query, (role,))
        staff = cursor.fetchall()
        cursor.close()
        
        return staff
    
    @staticmethod
    def create(first_name, last_name, role, email=None, contact_number=None):
        """Create a new staff member"""
        db = get_db_connection()
        cursor = db.cursor()
        
        query = """
            INSERT INTO Staff (FirstName, LastName, Role, Email, ContactNumber)
            VALUES (%s, %s, %s, %s, %s)
        """
        
        cursor.execute(query, (first_name, last_name, role, email, contact_number))
        db.commit()
        
        staff_id = cursor.lastrowid
        cursor.close()
        
        return staff_id
    
    @staticmethod
    def update(staff_id, data):
        """Update a staff member"""
        db = get_db_connection()
        cursor = db.cursor()
        
        set_clause = ", ".join([f"{key} = %s" for key in data.keys()])
        query = f"UPDATE Staff SET {set_clause} WHERE StaffID = %s"
        
        values = list(data.values())
        values.append(staff_id)
        
        cursor.execute(query, tuple(values))
        db.commit()
        
        affected_rows = cursor.rowcount
        cursor.close()
        
        return affected_rows
    
    @staticmethod
    def delete(staff_id):
        """Delete a staff member"""
        db = get_db_connection()
        cursor = db.cursor()
        
        query = "DELETE FROM Staff WHERE StaffID = %s"
        
        cursor.execute(query, (staff_id,))
        db.commit()
        
        affected_rows = cursor.rowcount
        cursor.close()
        
        return affected_rows
    
    @staticmethod
    def search(term):
        """Search staff members by name"""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = """
            SELECT * FROM Staff 
            WHERE FirstName LIKE %s OR LastName LIKE %s OR Role LIKE %s
            ORDER BY FirstName, LastName
        """
        
        term = f'%{term}%'
        cursor.execute(query, (term, term, term))
        staff = cursor.fetchall()
        cursor.close()
        
        return staff
