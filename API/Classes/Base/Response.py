from flask import jsonify

def api_response(success=True, message=None, data=None, error=None, status_code=200):
    """
    Standardized API response helper for MUIO.
    
    Args:
        success (bool): Whether the request was successful.
        message (str, optional): A human-readable message.
        data (dict|list, optional): The actual payload.
        error (str|dict, optional): Detailed error information.
        status_code (int): HTTP status code.
    
    Returns:
        tuple: (flask.Response, int) - A JSON response compatible with Flask's return type.
    """
    response = {
        "success": success,
        "message": message,
        "data": data,
        "error": error
    }
    return jsonify(response), status_code
