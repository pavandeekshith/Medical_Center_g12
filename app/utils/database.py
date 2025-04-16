import mysql.connector
from flask import current_app, g
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection(db_name=None):
    """
    Get a database connection.
    
    Args:
        db_name (str, optional): Database name to connect to.
            If None, connects to the default database.
    
    Returns:
        mysql.connector.connection: Database connection object
    """
    try:
        # Use the database name if provided, otherwise use default
        if db_name == 'cims':
            db_config = {
                'host': current_app.config['DB_HOST'],
                'user': current_app.config['DB_USER'],
                'password': current_app.config['DB_PASSWORD'],
                'database': current_app.config['CIMS_DB_NAME']
            }
        else:
            db_config = {
                'host': current_app.config['DB_HOST'],
                'user': current_app.config['DB_USER'],
                'password': current_app.config['DB_PASSWORD'],
                'database': current_app.config['DB_NAME']
            }
        
        # Create a new connection
        connection = mysql.connector.connect(**db_config)
        return connection
    
    except mysql.connector.Error as err:
        logger.error(f"Database connection error: {err}")
        raise

def close_db_connection(connection):
    """
    Close a database connection.
    
    Args:
        connection: Database connection to close
    """
    if connection:
        try:
            connection.close()
        except mysql.connector.Error as err:
            logger.error(f"Error closing database connection: {err}")

def execute_query(query, params=None, fetch=False, db_name=None):
    """
    Execute a SQL query.
    
    Args:
        query (str): SQL query to execute
        params (tuple, optional): Parameters for the query
        fetch (bool): Whether to fetch results
        db_name (str, optional): Database name to connect to
    
    Returns:
        If fetch is True, returns query results.
        If fetch is False, returns affected row count.
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
    
    except mysql.connector.Error as err:
        logger.error(f"Query execution error: {err}")
        if connection:
            connection.rollback()
        raise
    
    finally:
        if cursor:
            cursor.close()
        if connection:
            close_db_connection(connection)
