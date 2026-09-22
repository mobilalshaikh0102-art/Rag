"""
Flask API for Food Delivery Customer Support Chatbot
Production-ready with error handling and logging
"""

import os
import json
import logging
from datetime import datetime
from functools import wraps
from typing import Tuple, Dict

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from flask import Flask, request, jsonify
from flask_cors import CORS

# Import chatbot
try:
    from chatbot import RefundChatbot, CustomerOrder, RefundDecision
except ImportError:
    raise ImportError("chatbot.py not found. Ensure chatbot.py is in the same directory")

# ============= SETUP =============
app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize chatbot
try:
    chatbot = RefundChatbot()
    logger.info("✅ Chatbot initialized successfully")
except ValueError as e:
    logger.error(f"❌ Failed to initialize chatbot: {e}")
    chatbot = None


# ============= MIDDLEWARE & HELPERS =============

def handle_errors(f):
    """Decorator for consistent error handling"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            logger.warning(f"Validation Error: {e}")
            return jsonify({"error": str(e), "status": "validation_error"}), 400
        except json.JSONDecodeError as e:
            logger.warning(f"JSON Error: {e}")
            return jsonify({"error": "Invalid JSON format", "status": "json_error"}), 400
        except Exception as e:
            logger.error(f"Unexpected Error: {e}")
            return jsonify({"error": str(e), "status": "server_error"}), 500
    return decorated_function


def validate_api_key(f):
    """Decorator to validate API key in request headers"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get("X-API-Key")
        expected_key = os.environ.get("API_KEY", "default-dev-key")
        
        if not api_key or api_key != expected_key:
            logger.warning("Unauthorized API access attempt")
            return jsonify({"error": "Unauthorized", "status": "auth_error"}), 401
        
        return f(*args, **kwargs)
    return decorated_function


# ============= ROUTES =============

@app.route("/health", methods=["GET"])
def health_check() -> Tuple[Dict, int]:
    """Health check endpoint"""
    status = "healthy" if chatbot else "degraded"
    return jsonify({
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "chatbot_ready": chatbot is not None
    }), 200 if chatbot else 503


@app.route("/evaluate-refund", methods=["POST"])
@handle_errors
@validate_api_key
def evaluate_refund() -> Tuple[Dict, int]:
    """
    Evaluate a refund request
    
    Expected JSON payload:
    {
        "order_id": "string",
        "customer_id": "string",
        "order_total": number,
        "delivery_date": "YYYY-MM-DD",
        "order_status": "delivered|order_placed|cancelled",
        "delivery_time_minutes": number (optional),
        "refund_reason": "LATE_DELIVERY|QUALITY_ISSUE|MISSING_ITEMS|WRONG_ITEM",
        "has_photo_evidence": boolean,
        "previous_refunds": number,
        "days_since_order": number
    }
    """
    
    if not chatbot:
        return jsonify({"error": "Chatbot not initialized", "status": "service_error"}), 503
    
    # Validate request JSON
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON", "status": "validation_error"}), 400
    
    # Validate required fields
    required_fields = [
        "order_id", "customer_id", "order_total", "delivery_date",
        "order_status", "refund_reason", "days_since_order"
    ]
    
    missing_fields = [f for f in required_fields if f not in data]
    if missing_fields:
        return jsonify({
            "error": f"Missing required fields: {', '.join(missing_fields)}",
            "status": "validation_error"
        }), 400
    
    try:
        # Create order object
        order = CustomerOrder(
            order_id=str(data["order_id"]),
            customer_id=str(data["customer_id"]),
            order_total=float(data["order_total"]),
            delivery_date=str(data["delivery_date"]),
            order_status=str(data["order_status"]).lower(),
            delivery_time_minutes=data.get("delivery_time_minutes"),
            refund_reason=str(data["refund_reason"]).upper() if data.get("refund_reason") else None,
            has_photo_evidence=bool(data.get("has_photo_evidence", False)),
            previous_refunds=int(data.get("previous_refunds", 0)),
            days_since_order=int(data.get("days_since_order", 0))
        )
        
        # Evaluate refund
        logger.info(f"Evaluating refund for order: {order.order_id}")
        decision = chatbot.evaluate_refund(order)
        
        return jsonify({
            "order_id": order.order_id,
            "decision": decision.decision,
            "refund_amount": decision.refund_amount,
            "reason": decision.reason,
            "required_action": decision.required_action,
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except ValueError as e:
        logger.error(f"Value Error processing order: {e}")
        return jsonify({
            "error": f"Invalid input data: {str(e)}",
            "status": "validation_error"
        }), 400
    except Exception as e:
        logger.error(f"Error evaluating refund: {e}")
        raise


@app.route("/batch-evaluate", methods=["POST"])
@handle_errors
@validate_api_key
def batch_evaluate() -> Tuple[Dict, int]:
    """
    Evaluate multiple refund requests in batch
    
    Expected JSON payload:
    {
        "orders": [
            { refund request object },
            { refund request object },
            ...
        ]
    }
    """
    
    if not chatbot:
        return jsonify({"error": "Chatbot not initialized", "status": "service_error"}), 503
    
    data = request.get_json()
    if not data or "orders" not in data:
        return jsonify({
            "error": "Request must contain 'orders' array",
            "status": "validation_error"
        }), 400
    
    orders = data["orders"]
    if not isinstance(orders, list):
        return jsonify({
            "error": "'orders' must be an array",
            "status": "validation_error"
        }), 400
    
    results = []
    errors = []
    
    for idx, order_data in enumerate(orders):
        try:
            order = CustomerOrder(
                order_id=str(order_data["order_id"]),
                customer_id=str(order_data["customer_id"]),
                order_total=float(order_data["order_total"]),
                delivery_date=str(order_data["delivery_date"]),
                order_status=str(order_data["order_status"]).lower(),
                delivery_time_minutes=order_data.get("delivery_time_minutes"),
                refund_reason=str(order_data["refund_reason"]).upper() if order_data.get("refund_reason") else None,
                has_photo_evidence=bool(order_data.get("has_photo_evidence", False)),
                previous_refunds=int(order_data.get("previous_refunds", 0)),
                days_since_order=int(order_data.get("days_since_order", 0))
            )
            
            decision = chatbot.evaluate_refund(order)
            results.append({
                "order_id": order.order_id,
                "decision": decision.decision,
                "refund_amount": decision.refund_amount,
                "reason": decision.reason,
                "required_action": decision.required_action,
                "status": "success"
            })
            
        except Exception as e:
            errors.append({
                "order_index": idx,
                "error": str(e),
                "status": "error"
            })
    
    return jsonify({
        "processed": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors,
        "timestamp": datetime.now().isoformat()
    }), 200


@app.route("/audit-log", methods=["GET"])
@handle_errors
@validate_api_key
def get_audit_log() -> Tuple[Dict, int]:
    """Get audit trail of all decisions"""
    
    if not chatbot:
        return jsonify({"error": "Chatbot not initialized", "status": "service_error"}), 503
    
    audit_log = json.loads(chatbot.get_audit_log())
    return jsonify({
        "total_decisions": len(audit_log),
        "decisions": audit_log,
        "timestamp": datetime.now().isoformat()
    }), 200


@app.route("/stats", methods=["GET"])
@handle_errors
@validate_api_key
def get_stats() -> Tuple[Dict, int]:
    """Get decision statistics"""
    
    if not chatbot:
        return jsonify({"error": "Chatbot not initialized", "status": "service_error"}), 503
    
    decisions = json.loads(chatbot.get_audit_log())
    
    stats = {
        "total_decisions": len(decisions),
        "approved": sum(1 for d in decisions if d["decision"] == "APPROVE"),
        "declined": sum(1 for d in decisions if d["decision"] == "DECLINE"),
        "needs_review": sum(1 for d in decisions if d["decision"] == "NEEDS_REVIEW"),
        "total_refunded": sum(d["refund_amount"] for d in decisions if d["decision"] == "APPROVE"),
        "timestamp": datetime.now().isoformat()
    }
    
    return jsonify(stats), 200


# ============= ERROR HANDLERS =============

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        "error": "Endpoint not found",
        "status": "not_found",
        "timestamp": datetime.now().isoformat()
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors"""
    return jsonify({
        "error": "Method not allowed",
        "status": "method_not_allowed",
        "timestamp": datetime.now().isoformat()
    }), 405


# ============= STARTUP =============

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    
    logger.info(f"🚀 Starting chatbot API on port {port}")
    logger.info(f"Debug mode: {debug}")
    
    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug,
        threaded=True
    )
