from flask import Flask, request, jsonify
from flasgger import Swagger
from functools import wraps
import os
import logging
import tiktoken


app = Flask(__name__)
swagger = Swagger(app)

log_formatter = logging.Formatter(
    '[%(asctime)s] %(levelname)s in %(module)s: %(message)s')
# ==============================================================================
# 🛠️ EDIT ZONE: ADD OR CHANGE YOUR OPERATIONS HERE
# ==============================================================================



def wordCount(text: str) -> int:
    """Counts words."""
    return len(text.split()) if text else 0


def textUpper(text: str) -> str:
    """Converts to UPPERCASE."""
    return text.upper() if text else ""


def textReverse(text: str) -> str:
    """Reverses text order."""
    return text[::-1] if text else ""


def textClean(text: str) -> str:
    """Trims starting and ending spaces."""
    return text.strip() if text else ""
def textSplit(text: str) ->list:
    """give the list of strings"""
    return list(text.split())

def count_openai_tokens(text: str, model_name: str = "gpt-4") -> int:
    # Automatically get the correct encoding for the specified model
    encoding = tiktoken.encoding_for_model(model_name)
    num_tokens = len(encoding.encode(text))
    return num_tokens


# Simply add your new function names to this registry list to active them!
DICT_OF_OPERATIONS = {
    "wordCount": wordCount,
    "textUpper": textUpper,
    "textReverse": textReverse,
    "textClean": textClean,
    "textSplit": textSplit,
    "textTokenCounter":count_openai_tokens
}

# ==============================================================================
# GUARD LAYER (Handles Authentication & Missing Parameters automatically)
# ==============================================================================
API_SECRET_KEY = os.getenv("API_SECRET_KEY", "my_secure_dev_key_123")


def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.headers.get("X-API-Key") != API_SECRET_KEY:
            return jsonify({"error": "Invalid or missing X-API-Key header"}), 401
        return f(*args, **kwargs)

    return decorated


def require_payload(required_fields):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            data = request.get_json(silent=True) or {}
            for field in required_fields:
                val = data.get(field)
                if not val or not isinstance(val, list):
                    return jsonify({"error": f"Field '{field}' must be a non-empty array"}), 400
            return f(*args, **kwargs)

        return decorated

    return decorator


# ==============================================================================
# 🚀 THE API ROUTE (You never need to edit this logic!)
# ==============================================================================

@app.route('/api/process', methods=['POST'])
@require_api_key
@require_payload(['operations', 'inputs'])
def process_data():
    """
    Process multiple items with multiple logic engines simultaneously.
    ---
    parameters:
      - name: X-API-Key
        in: header
        type: string
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            operations:
              type: array
              items:
                type: string
              example: ["textUpper", "wordCount"]
            inputs:
              type: array
              items:
                type: string
              example: [" hello world ", "flask api"]
    responses:
      200:
        description: Request processed successfully.
    """
    data = request.get_json()

    consolidated_results = []

    # Loop through each item provided in your input array
    for current_text in data['inputs']:
        text_results = {}

        # Run every requested tool engine on this specific text item
        for op_name in data['operations']:
            action = DICT_OF_OPERATIONS.get(op_name)

            if action:
                text_results[op_name] = action(str(current_text))
            else:
                text_results[op_name] = "Unsupported operation"

        # Bundle it cleanly into the final report
        consolidated_results.append({
            "input_string": current_text,
            "results": text_results
        })
        app.logger.info("📤 Request complete. Consolidated report dispatched successfully.")

    return jsonify({
        "status": "success",
        "processed_metrics": consolidated_results
    }), 200


if __name__ == '__main__':
    app.run(port=5000, debug=True)
