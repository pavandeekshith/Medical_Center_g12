import bcrypt
import jwt
import datetime
from app.utils.database import get_db_connection

def validate_login(db,username, password):
    try:
        cursor = db.cursor(dictionary=True)
        
        # Use the provided SQL query for verification
        query = """
        SELECT
            l.MemberID, l.Password, l.Role, l.Session,
            m.ID, m.UserName, m.emailID
        FROM Login l
        JOIN members m ON CAST(l.MemberID AS UNSIGNED) = m.ID
        WHERE m.UserName = %s AND l.Password = %s
        """
        
        cursor.execute(query, (username, password))
        user = cursor.fetchone()
        
        if user:
            # Create a new session for the user
            # session = get_session(db, user['MemberID'], user['UserName'], user['Role'])
            return user
        
        return None
    except Exception as e:
        print(f"Login verification error: {e}")
        return None


def get_user_role(db, user_id):
    """
    Get the role of a user
    
    Args:
        db: Database connection
        user_id: User ID
        
    Returns:
        str: User role
    """
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute('SELECT Role FROM Login WHERE MemberID = %s', (user_id,))
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            return result['Role']
        return None
    except Exception as e:
        print(f"Error getting user role: {e}")
        return None

def get_session(db, user_id, username, role="user", group=12):
    """
    Generate a JWT session token and update it in the database.
    
    Args:
        db: Database connection object
        user_id (str): The user's member ID
        username (str): The user's name
        role (str): The user's role (default: "user")
        group (int): The user's group ID (default: 12)
        
    Returns:
        dict: Session information including token, expiry time and user details
    """
    try:
        cursor = db.cursor()
        
        # Generate JWT token with 1 hour expiry
        expiry_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
        expiry_timestamp = int(expiry_time.timestamp())
        
        token = jwt.encode({
            "user": username,
            "role": role,
            "exp": expiry_timestamp,
            "group": group,
            "session_id": user_id
        }, "CS", algorithm="HS256")
        
        # Update database with new session
        cursor.execute(
            'UPDATE Login SET Session = %s, Expiry = %s WHERE MemberID = %s',
            (token, expiry_timestamp, user_id)
        )
        
        db.commit()
        cursor.close()
        
        # Return session information
        return {
            "token": token,
            "expires": expiry_timestamp,
            "user_id": user_id,
            "username": username,
            "role": role
        }
    except Exception as e:
        print(f"Error generating session: {e}")
        return None
