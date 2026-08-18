from flask import Flask, request, jsonify, redirect, url_for
from flasgger import Swagger
from functools import wraps
import os
import logging
import tiktoken
import uuid
app = Flask(__name__)
log_formatter = logging.Formatter('[CRID: %(crid)s] %(levelname)s in %(module)s: %(message)s')

handler = logging.StreamHandler()
handler.setFormatter(log_formatter)

base_logger = logging.getLogger("my_app")
base_logger.setLevel(logging.INFO)
base_logger.addHandler(handler)



# ==============================================================================
#  EDIT ZONE: ADD OR CHANGE YOUR OPERATIONS HERE
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


def textSplit(text: str) -> list:
    """give the list of strings"""
    return list(text.split())


def count_openai_tokens(text: str, model_name: str = "gpt-4") -> object:
    encoding = tiktoken.encoding_for_model(model_name)
    num_tokens = len(encoding.encode(text))

    return {"Tokenised Text": list(encoding.encode(text)), "Number of tokens": num_tokens}


DICT_OF_OPERATIONS = {
    "wordCount": wordCount,
    "textUpper": textUpper,
    "textReverse": textReverse,
    "textClean": textClean,
    "textSplit": textSplit,
    "textTokenCounter": count_openai_tokens
}
enum_list= list(DICT_OF_OPERATIONS.keys())

# ==============================================================================
# GUARD LAYER (Handles Authentication & Missing Parameters automatically)
# ==============================================================================
API_SECRET_KEY = os.getenv("API_SECRET_KEY", "my_secure_dev_key_123")
swagger = Swagger(app)


def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.headers.get("X-API-Key") != API_SECRET_KEY:
            logging.info("User tried wrong x-api-key",)
            return jsonify({"error": "Invalid or missing X-API-Key header"}), 401
        return f(*args, **kwargs)

    return decorated


def require_payload():
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # 1. Validate operations from query parameters

            operations = request.args.getlist('operations')
            if not operations:
                return jsonify({"error": "Query parameter 'operations' must be a non-empty array"}), 400

            # 2. Validate inputs from JSON body
            data = request.get_json(silent=True) or {}
            inputs = data.get('inputs')

            if not inputs or not isinstance(inputs, list):
                logging.error("")
                return jsonify({"error": "Field 'inputs' must be a non-empty array in the JSON body"}), 400


            for s in inputs:
                if len(str(s)) > 128 or len(str(s)) == 0:
                    return jsonify({"error": "input validation doesnt match expectations"}), 400

            return f(*args, **kwargs)

        return decorated

    return decorator


# ==============================================================================
# 🚀 THE API ROUTE
# ==============================================================================
@app.route('/', methods=['GET'])
def Home():
    return redirect(url_for('apidocs'))


@app.route('/api/process', methods=['POST'])
@require_api_key
@require_payload()
def process_data():
    """
    Process multiple items with multiple logic engines simultaneously.

    ️ **Input Validation Rules:**
    1. **Authentication**: A valid `X-API-Key` credential must be provided in the header.
    2. **operations**: A query string array containing at least 1 engine option.
    3. **inputs**: A JSON body array containing text items.
       * Array cannot be empty.
       * Each text string must be between **1 and 128 characters** long.
    ---
    parameters:
      - name: X-API-Key
        in: header
        type: string
        required: true
        description: Private secret key to authorize access.
      - name: operations
        in: query
        type: array
        items:
          type: string
          enum: ["wordCount", "textUpper", "textReverse", "textClean", "textSplit", "textTokenCounter"]
        collectionFormat: multi
        required: true
        minItems: 1
        description: List of transformation or analytical logic engines to execute. Select at least one.
        example: ["textUpper", "textTokenCounter"]
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - inputs
          properties:
            inputs:
              type: array
              minItems: 1
              description: Non-empty array of strings. Individual strings must be 1-128 characters.
              items:
                type: string
                minLength: 1
                maxLength: 128
              example: [" hello world ", "flask api"]
    responses:
      200:
        description: Request processed successfully. Returns execution metrics for each input.
      400:
        description: Validation error. Parameters missing or string length constraints violated.
      401:
        description: Unauthorized. Missing or invalid X-API-Key header.
    """
    # Extract data from both query string and JSON body
    try:
        current_crid = str(uuid.uuid4())[:8]
        logger = logging.LoggerAdapter(base_logger, {"crid": current_crid})
        operations = request.args.getlist('operations')
        data = request.get_json()

        consolidated_results = []


        for current_text in data['inputs']:
            text_results = {}
            for op_name in operations:
                action = DICT_OF_OPERATIONS.get(op_name)
                if action:
                    text_results[op_name] = action(str(current_text))
                    logger.info(f'operation {op_name} was executed')
                else:
                    text_results[op_name] = "Unsupported operation"
                    logger.error(f"User is trying {op_name} which does not exist")

            consolidated_results.append({
                "input_string": current_text,
                "results": text_results
            })

        app.logger.info("📤 Request complete. Consolidated report dispatched successfully.")
        return jsonify({
            "status": "success",
            "processed_metrics": consolidated_results
        }), 200 , {"CRID": current_crid}
    except:
        return jsonify({"error": "Internal Server Error"}), 500


if __name__ == '__main__':
    app.run(port=5000, debug=True)
