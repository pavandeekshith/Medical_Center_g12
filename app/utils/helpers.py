import datetime
import hashlib
import re
import logging
from flask import session, request, current_app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def format_date(date_str):
    """
    Format a date string to a more readable format.
    
    Args:
        date_str (str): Date string in 'YYYY-MM-DD' format
    
    Returns:
        str: Formatted date string
    """
    try:
        date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d')
        return date_obj.strftime('%B %d, %Y')
    except (ValueError, TypeError):
        return date_str

def format_time(time_str):
    """
    Format a time string to a more readable format.
    
    Args:
        time_str (str): Time string in 'HH:MM:SS' format
    
    Returns:
        str: Formatted time string
    """
    try:
        time_obj = datetime.datetime.strptime(time_str, '%H:%M:%S')
        return time_obj.strftime('%I:%M %p')
    except (ValueError, TypeError):
        return time_str

def get_current_date():
    """
    Get the current date in 'YYYY-MM-DD' format.
    
    Returns:
        str: Current date
    """
    return datetime.datetime.now().strftime('%Y-%m-%d')

def get_current_time():
    """
    Get the current time in 'HH:MM:SS' format.
    
    Returns:
        str: Current time
    """
    return datetime.datetime.now().strftime('%H:%M:%S')

def is_valid_email(email):
    """
    Check if an email address is valid.
    
    Args:
        email (str): Email address to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_valid_phone(phone):
    """
    Check if a phone number is valid.
    
    Args:
        phone (str): Phone number to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    pattern = r'^\+?[0-9]{10,15}$'
    return re.match(pattern, phone) is not None

def generate_hash(text):
    """
    Generate a SHA-256 hash of the given text.
    
    Args:
        text (str): Text to hash
    
    Returns:
        str: Hashed text
    """
    return hashlib.sha256(text.encode()).hexdigest()

def is_authenticated():
    """
    Check if the current user is authenticated.
    
    Returns:
        bool: True if authenticated, False otherwise
    """
    return 'user_id' in session and 'token' in session

def get_user_role():
    """
    Get the role of the current user.
    
    Returns:
        str: User role or None if not authenticated
    """
    return session.get('role')

def log_activity(activity_type, description, user_id=None):
    """
    Log user activity.
    
    Args:
        activity_type (str): Type of activity
        description (str): Activity description
        user_id (str, optional): User ID. If None, uses the current user's ID
    """
    try:
        if user_id is None and 'user_id' in session:
            user_id = session['user_id']
        
        if user_id:
            from app.utils.database import execute_query
            
            query = """
                INSERT INTO ActivityLog (UserID, ActivityType, Description, Timestamp, IPAddress)
                VALUES (%s, %s, %s, %s, %s)
            """
            
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ip_address = request.remote_addr
            
            execute_query(query, (user_id, activity_type, description, timestamp, ip_address))
            logger.info(f"Activity logged: {activity_type} by {user_id}")
    except Exception as e:
        logger.error(f"Error logging activity: {e}")

def check_permission(user_role, resource, action):
    """
    Check if a user has permission to perform an action on a resource.
    
    Args:
        user_role (str): User role
        resource (str): Resource to access
        action (str): Action to perform
    
    Returns:
        bool: True if permitted, False otherwise
    """
    # Define permission matrix
    permissions = {
        'doctor': {
            'appointments': ['view', 'create', 'update', 'delete'],
            'prescriptions': ['view', 'create', 'update'],
            'availability': ['view', 'create', 'update', 'delete'],
            'students': ['view'],
            'medications': ['view']
        },
        'staff': {
            'prescriptions': ['view', 'update'],
            'medications': ['view', 'create', 'update', 'delete'],
            'students': ['view'],
            'appointments': ['view']
        },
        'student': {
            'appointments': ['view', 'create', 'update', 'delete'],
            'prescriptions': ['view'],
            'doctors': ['view']
        }
    }
    
    # Check if role has access to the resource and action
    if user_role in permissions and resource in permissions[user_role]:
        return action in permissions[user_role][resource]
    
    return False

def sanitize_input(text):
    """
    Sanitize user input to prevent XSS attacks.
    
    Args:
        text (str): Text to sanitize
    
    Returns:
        str: Sanitized text
    """
    if text is None:
        return None
    
    # Replace potentially dangerous characters
    sanitized = text.replace('<', '&lt;').replace('>', '&gt;')
    sanitized = sanitized.replace('"', '&quot;').replace("'", '&#39;')
    
    return sanitized

def validate_date_format(date_str):
    """
    Validate if a string is in the correct date format (YYYY-MM-DD).
    
    Args:
        date_str (str): Date string to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        datetime.datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def validate_time_format(time_str):
    """
    Validate if a string is in the correct time format (HH:MM:SS).
    
    Args:
        time_str (str): Time string to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        datetime.datetime.strptime(time_str, '%H:%M:%S')
        return True
    except ValueError:
        return False

def get_pagination_params(request):
    """
    Get pagination parameters from request.
    
    Args:
        request: Flask request object
    
    Returns:
        tuple: (page, per_page)
    """
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        # Ensure valid values
        page = max(1, page)
        per_page = max(1, min(100, per_page))  # Limit per_page between 1 and 100
        
        return page, per_page
    except (ValueError, TypeError):
        return 1, 10

def paginate_results(items, page, per_page):
    """
    Paginate a list of items.
    
    Args:
        items (list): List of items to paginate
        page (int): Page number
        per_page (int): Items per page
    
    Returns:
        dict: Pagination information and items for the current page
    """
    total_items = len(items)
    total_pages = (total_items + per_page - 1) // per_page  # Ceiling division
    
    # Ensure page is within valid range
    page = min(max(1, page), total_pages) if total_pages > 0 else 1
    
    # Calculate start and end indices
    start_idx = (page - 1) * per_page
    end_idx = min(start_idx + per_page, total_items)
    
    # Get items for the current page
    current_items = items[start_idx:end_idx] if total_items > 0 else []
    
    return {
        'items': current_items,
        'page': page,
        'per_page': per_page,
        'total_items': total_items,
        'total_pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages
    }

def generate_random_password(length=10):
    """
    Generate a random password.
    
    Args:
        length (int): Password length
    
    Returns:
        str: Random password
    """
    import random
    import string
    
    # Define character sets
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special = '!@#$%^&*()-_=+'
    
    # Ensure at least one character from each set
    password = [
        random.choice(lowercase),
        random.choice(uppercase),
        random.choice(digits),
        random.choice(special)
    ]
    
    # Fill the rest of the password
    remaining_length = length - len(password)
    all_chars = lowercase + uppercase + digits + special
    
    password.extend(random.choice(all_chars) for _ in range(remaining_length))
    
    # Shuffle the password characters
    random.shuffle(password)
    
    return ''.join(password)
