from flask import Blueprint, request, jsonify
from app.models.doctors import DoctorAvailability
from datetime import datetime

api = Blueprint('api', __name__)

@api.route('/appointments/availability', methods=['GET'])
def get_available_slots():
    """API endpoint for getting available appointment slots."""
    doctor_id = request.args.get('doctor_id')
    date = request.args.get('date')
    
    if not doctor_id or not date:
        return jsonify({'success': False, 'message': 'Missing required parameters'}), 400
    
    try:
        # Get available slots
        slots = DoctorAvailability.get_available_slots(doctor_id, date)
        
        # Format slots for frontend
        formatted_slots = []
        for slot in slots:
            # Format time string (if needed)
            time_str = slot.get('time', '')
            if time_str and ':' in time_str:
                time_parts = time_str.split(':')
                time_display = f"{time_parts[0]}:{time_parts[1]}"
            else:
                time_display = time_str
                
            formatted_slots.append({
                'time': time_display,
                'status': slot.get('status', 'Unknown').capitalize()
            })
            
        return jsonify({
            'success': True,
            'slots': formatted_slots
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500