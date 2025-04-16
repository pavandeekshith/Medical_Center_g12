from app.utils.database import get_db_connection

class Medication:
    def __init__(self, medication_id=None, name=None, dosage_form=None,
                 quantity_in_stock=None, expiry_date=None):
        self.medication_id = medication_id
        self.name = name
        self.dosage_form = dosage_form
        self.quantity_in_stock = quantity_in_stock
        self.expiry_date = expiry_date
    
    @staticmethod
    def get_all():
        """Get all medications"""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = "SELECT * FROM Medications ORDER BY Name"
        
        cursor.execute(query)
        medications = cursor.fetchall()
        cursor.close()
        
        return medications
    
    @staticmethod
    def get_by_id(medication_id):
        """Get medication by ID"""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = "SELECT * FROM Medications WHERE MedicationID = %s"
        
        cursor.execute(query, (medication_id,))
        medication = cursor.fetchone()
        cursor.close()
        
        return medication
    
    @staticmethod
    def search(term):
        """Search medications by name"""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = "SELECT * FROM Medications WHERE Name LIKE %s ORDER BY Name"
        
        cursor.execute(query, (f'%{term}%',))
        medications = cursor.fetchall()
        cursor.close()
        
        return medications
    
    @staticmethod
    def create(name, dosage_form, quantity_in_stock, expiry_date=None):
        """Create a new medication"""
        db = get_db_connection()
        cursor = db.cursor()
        
        if expiry_date:
            query = """
                INSERT INTO Medications (Name, DosageForm, QuantityInStock, ExpiryDate)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (name, dosage_form, quantity_in_stock, expiry_date))
        else:
            query = """
                INSERT INTO Medications (Name, DosageForm, QuantityInStock)
                VALUES (%s, %s, %s)
            """
            cursor.execute(query, (name, dosage_form, quantity_in_stock))
        
        db.commit()
        
        medication_id = cursor.lastrowid
        cursor.close()
        
        return medication_id
    
    @staticmethod
    def update(medication_id, data):
        """Update a medication"""
        db = get_db_connection()
        cursor = db.cursor()
        
        set_clause = ", ".join([f"{key} = %s" for key in data.keys()])
        query = f"UPDATE Medications SET {set_clause} WHERE MedicationID = %s"
        
        values = list(data.values())
        values.append(medication_id)
        
        cursor.execute(query, tuple(values))
        db.commit()
        
        affected_rows = cursor.rowcount
        cursor.close()
        
        return affected_rows
    
    @staticmethod
    def delete(medication_id):
        """Delete a medication"""
        db = get_db_connection()
        cursor = db.cursor()
        
        query = "DELETE FROM Medications WHERE MedicationID = %s"
        
        cursor.execute(query, (medication_id,))
        db.commit()
        
        affected_rows = cursor.rowcount
        cursor.close()
        
        return affected_rows
    
    @staticmethod
    def update_stock(medication_id, quantity_change):
        """Update medication stock quantity"""
        db = get_db_connection()
        cursor = db.cursor()
        
        query = """
            UPDATE Medications 
            SET QuantityInStock = QuantityInStock + (%s) 
            WHERE MedicationID = %s AND (QuantityInStock + %s) >= 0
        """
        
        cursor.execute(query, (quantity_change, medication_id, quantity_change))
        db.commit()
        
        affected_rows = cursor.rowcount
        cursor.close()
        
        return affected_rows
    
    @staticmethod
    def get_low_stock(threshold=10):
        """Get medications with low stock"""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = "SELECT * FROM Medications WHERE QuantityInStock <= %s ORDER BY QuantityInStock"
        
        cursor.execute(query, (threshold,))
        medications = cursor.fetchall()
        cursor.close()
        
        return medications
    
    @staticmethod
    def get_expired(current_date):
        """Get expired medications"""
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = "SELECT * FROM Medications WHERE ExpiryDate IS NOT NULL AND ExpiryDate <= %s"
        
        cursor.execute(query, (current_date,))
        medications = cursor.fetchall()
        cursor.close()
        
        return medications
