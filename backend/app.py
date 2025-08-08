import firebase_admin
from firebase_admin import credentials, firestore, auth
from firebase_admin.firestore import FieldFilter
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import random
import razorpay
from math import radians, sin, cos, sqrt, atan2

load_dotenv()
app = Flask(__name__)
CORS(app)

# --- INITIALIZATION ---
try:
    cred_path = os.getenv('FIREBASE_credentials_PATH')
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Firebase Admin initialized successfully.")
except Exception as e:
    print(f"!!! ERROR initializing Firebase Admin: {e}")
    db = None
try:
    razorpay_client = razorpay.Client(auth=(os.getenv("RAZORPAY_KEY_ID"), os.getenv("RAZORPAY_KEY_SECRET")))
    print("Razorpay client initialized successfully.")
except Exception as e:
    print(f"Could not initialize Razorpay client: {e}")
    razorpay_client = None

# --- HELPER FUNCTIONS ---
def get_user_from_token(request):
    auth_header = request.headers.get('Authorization')
    if not auth_header or "Bearer " not in auth_header:
        return None, (jsonify({"error": "Missing or invalid Authorization header"}), 401)
    id_token = auth_header.split("Bearer ")[1]
    try:
        return auth.verify_id_token(id_token), None
    except Exception as e:
        return None, (jsonify({"error": "Unauthorized", "details": str(e)}), 401)

def convert_geopoints(doc_dict):
    for field in ['pickupLocation', 'dropoffLocation', 'riderLocation', 'lastKnownLocation', 'pickupConfirmationLocation', 'deliveryConfirmationLocation']:
        if doc_dict.get(field) and isinstance(doc_dict[field], firestore.GeoPoint):
            geopoint = doc_dict[field]
            doc_dict[field] = {'latitude': geopoint.latitude, 'longitude': geopoint.longitude}
    return doc_dict

# --- USER & PROFILE ENDPOINTS ---
@app.route("/api/submit-profile", methods=["POST"])
def submit_profile():
    decoded_token, error = get_user_from_token(request);
    if error: return error
    uid = decoded_token['uid']; phone_number = decoded_token.get('phone_number', ''); data = request.get_json()
    if not data or not all(k in data for k in ["name", "email", "role", "dob", "aadhar"]):
        return jsonify({"error": "Missing required profile fields"}), 400
    role = data.get("role")
    if role not in ["sender", "rider"]: return jsonify({"error": "Invalid role specified"}), 400
    user_data = {"uid": uid, "phoneNumber": phone_number, "name": data["name"], "email": data["email"], "dob": data["dob"], "aadhar": data["aadhar"], "createdAt": firestore.SERVER_TIMESTAMP, "kycStatus": "verified", "roles": [role], "isOnline": False, "rating": 0, "ratingCount": 0}
    db.collection("users").document(uid).set(user_data, merge=True)
    return jsonify({"status": "Profile submitted successfully", "uid": uid}), 200

@app.route("/api/users/<user_id>", methods=["GET"])
def get_user_profile(user_id):
    decoded_token, error = get_user_from_token(request);
    if error: return error
    user_ref = db.collection("users").document(user_id); user_doc = user_ref.get()
    if not user_doc.exists: return jsonify({"error": "User not found"}), 404
    user_data = user_doc.to_dict()
    public_profile = {"name": user_data.get("name"), "phoneNumber": user_data.get("phoneNumber"), "rating": user_data.get("rating", 0), "ratingCount": user_data.get("ratingCount", 0)}
    return jsonify(public_profile), 200

# --- P2P TASK ENDPOINTS ---
@app.route("/api/tasks/create", methods=["POST"])
def create_task():
    decoded_token, error = get_user_from_token(request)
    if error: return error
    data = request.get_json()
    required = ["pickupAddress", "dropoffAddress", "pickupLocation", "dropoffLocation", "itemDescription", "fee", "recipientName", "recipientPhone"]
    if not all(k in data for k in required): return jsonify({"error": "Missing required fields"}), 400
    try:
        pickup_lat, pickup_lng = float(data["pickupLocation"]['lat']), float(data["pickupLocation"]['lng'])
        dropoff_lat, dropoff_lng = float(data["dropoffLocation"]['lat']), float(data["dropoffLocation"]['lng'])
    except (ValueError, TypeError, KeyError): return jsonify({"error": "Invalid location data format"}), 400
    task_ref = db.collection("p2p_tasks").document()
    task_data = {"taskId": task_ref.id, "senderId": decoded_token['uid'], "riderId": None, "pickupAddress": data["pickupAddress"], "dropoffAddress": data["dropoffAddress"], "pickupLocation": firestore.GeoPoint(pickup_lat, pickup_lng), "dropoffLocation": firestore.GeoPoint(dropoff_lat, dropoff_lng), "itemDescription": data["itemDescription"], "recipientName": data["recipientName"], "recipientPhone": data["recipientPhone"], "status": "draft", "fee": data["fee"], "createdAt": firestore.SERVER_TIMESTAMP, "pickupPIN": str(random.randint(1000,9999)), "deliveryPIN": str(random.randint(1000,9999))}
    task_ref.set(task_data)
    return jsonify({"taskId": task_ref.id, "status": "draft"}), 200

@app.route("/api/tasks/status/<task_id>", methods=["GET"])
def get_task_status(task_id):
    decoded_token, error = get_user_from_token(request);
    if error: return error
    task_ref = db.collection("p2p_tasks").document(task_id); task_doc = task_ref.get()
    if not task_doc.exists: return jsonify({"error": "Task not found"}), 404
    return jsonify(convert_geopoints(task_doc.to_dict())), 200

@app.route("/api/tasks/update-status", methods=["POST"])
def update_task_status():
    decoded_token, error = get_user_from_token(request);
    if error: return error
    uid = decoded_token['uid']; data = request.get_json()
    task_id, new_status, pin, location = data.get("taskId"), data.get("status"), data.get("pin"), data.get("location")
    if not task_id or not new_status: return jsonify({"error": "Missing taskId or new status"}), 400
    if new_status not in ["in_transit", "delivered"]: return jsonify({"error": "Invalid status update"}), 400
    task_ref = db.collection("p2p_tasks").document(task_id); task_doc = task_ref.get()
    if not task_doc.exists: return jsonify({"error": "Task not found"}), 404
    task_data = task_doc.to_dict()
    if task_data.get("riderId") != uid: return jsonify({"error": "Not authorized to update this task"}), 403
    if new_status == "in_transit" and pin != task_data.get("pickupPIN"): return jsonify({"error": "Invalid Pickup PIN"}), 400
    if new_status == "delivered" and pin != task_data.get("deliveryPIN"): return jsonify({"error": "Invalid Delivery PIN"}), 400
    update_payload = {"status": new_status}
    if location:
        geo_point = firestore.GeoPoint(location['lat'], location['lng'])
        if new_status == "in_transit": update_payload["pickupConfirmationLocation"] = geo_point
        elif new_status == "delivered": update_payload["deliveryConfirmationLocation"] = geo_point
    task_ref.update(update_payload)
    if new_status == "delivered":
        settle_payment_for_task(task_data)
    return jsonify({"status": "success", "message": f"Task status updated to {new_status}"}), 200

# --- PAYMENT & TRANSACTION ENDPOINTS ---
@app.route("/api/payments/create-order", methods=["POST"])
def create_payment_order():
    decoded_token, error = get_user_from_token(request);
    if error: return error
    data = request.get_json()
    if not data or "amount" not in data or "taskId" not in data: return jsonify({"error": "Amount and taskId are required"}), 400
    amount_paise = int(data["amount"] * 100)
    if not razorpay_client: return jsonify({"error": "Payment gateway not configured"}), 500
    try:
        razorpay_order = razorpay_client.order.create({"amount": amount_paise, "currency": "INR", "receipt": data["taskId"], "payment_capture": 1})
        return jsonify({"orderId": razorpay_order["id"], "amount": amount_paise, "razorpayKey": os.getenv("RAZORPAY_KEY_ID")}), 200
    except Exception as e: return jsonify({"error": "Could not create payment order", "details": str(e)}), 500

@app.route("/api/payments/verify", methods=["POST"])
def verify_payment_and_assign():
    decoded_token, error = get_user_from_token(request);
    if error: return error
    data = request.get_json()
    required = ["razorpay_payment_id", "razorpay_order_id", "razorpay_signature", "taskId", "riderId"]
    if not all(k in data for k in required): return jsonify({"error": "Missing payment verification fields"}), 400
    try:
        params_dict = {'razorpay_order_id': data['razorpay_order_id'], 'razorpay_payment_id': data['razorpay_payment_id'], 'razorpay_signature': data['razorpay_signature']}
        razorpay_client.utility.verify_payment_signature(params_dict)
        task_ref = db.collection("p2p_tasks").document(data['taskId'])
        task_ref.update({"riderId": data['riderId'], "status": "pending_acceptance", "orderId": data['razorpay_order_id'], "paymentId": data['razorpay_payment_id']})
        return jsonify({"status": "success", "message": "Payment verified and rider assigned"}), 200
    except Exception as e:
        print(f"!!! PAYMENT VERIFICATION FAILED: {e}")
        return jsonify({"error": "Payment verification failed", "details": str(e)}), 400

def settle_payment_for_task(task_data):
    try:
        rider_id, sender_id, total_fee = task_data.get("riderId"), task_data.get("senderId"), float(task_data.get("fee", 0))
        platform_fee = round(total_fee * 0.05, 2)
        if platform_fee < 5: platform_fee = 5
        rider_payout = total_fee - platform_fee
        print(f"--- SIMULATING PAYMENT SETTLEMENT for Task {task_data['taskId']} ---")
        print(f"Rider Payout: {rider_payout}")
        print("------------------------------------------------------")
        transaction_ref = db.collection("transactions").document()
        transaction_ref.set({"transactionId": transaction_ref.id, "taskId": task_data['taskId'], "senderId": sender_id, "riderId": rider_id, "totalAmount": total_fee, "platformFee": platform_fee, "riderPayout": rider_payout, "status": "settled", "createdAt": firestore.SERVER_TIMESTAMP})
        return True
    except Exception as e:
        print(f"!!! ERROR during payment settlement for task {task_data['taskId']}: {e}")
        return False

@app.route("/api/transactions/history", methods=["GET"])
def get_transaction_history():
    decoded_token, error = get_user_from_token(request);
    if error: return error
    uid = decoded_token['uid']
    sent_q = db.collection("transactions").where(filter=FieldFilter("senderId", "==", uid)).stream()
    received_q = db.collection("transactions").where(filter=FieldFilter("riderId", "==", uid)).stream()
    transactions = [tx.to_dict() for tx in sent_q]
    tx_ids = {t['transactionId'] for t in transactions}
    for tx in received_q: 
        if tx.id not in tx_ids: transactions.append(tx.to_dict())
    transactions.sort(key=lambda x: x['createdAt'], reverse=True)
    return jsonify({"transactions": transactions}), 200

# --- RIDER & FEEDBACK ENDPOINTS ---
@app.route("/api/rider/status", methods=["POST"])
def set_rider_status():
    decoded_token, error = get_user_from_token(request);
    if error: return error
    data = request.get_json(); is_online = data.get("isOnline"); location = data.get("location")
    if is_online is None: return jsonify({"error": "Missing 'isOnline' field"}), 400
    user_ref = db.collection("users").document(decoded_token['uid']); update_data = {"isOnline": is_online}
    if is_online and location: update_data["lastKnownLocation"] = firestore.GeoPoint(location['lat'], location['lng'])
    user_ref.update(update_data)
    return jsonify({"status": f"Rider status updated to {'online' if is_online else 'offline'}"}), 200

@app.route("/api/riders/online", methods=["GET"])
def get_online_riders():
    decoded_token, error = get_user_from_token(request);
    if error: return error
    riders_ref = db.collection("users").where(filter=FieldFilter("roles", "array_contains", "rider")).where(filter=FieldFilter("isOnline", "==", True)).stream()
    online_riders = []
    for rider in riders_ref:
        rider_data = convert_geopoints(rider.to_dict())
        online_riders.append({"uid": rider_data.get("uid"), "name": rider_data.get("name"), "rating": rider_data.get("rating", 0), "ratingCount": rider_data.get("ratingCount", 0), "location": rider_data.get("lastKnownLocation")})
    return jsonify({"riders": online_riders}), 200

@app.route("/api/tasks/available", methods=["GET"])
def get_available_tasks():
    decoded_token, error = get_user_from_token(request);
    if error: return error
    uid = decoded_token['uid']
    tasks_ref = db.collection("p2p_tasks").where(filter=FieldFilter("riderId", "==", uid)).where(filter=FieldFilter("status", "==", "pending_acceptance")).stream()
    assigned_tasks = [convert_geopoints(task.to_dict()) for task in tasks_ref]
    return jsonify({"tasks": assigned_tasks}), 200

@app.route("/api/tasks/active", methods=["GET"])
def get_active_tasks():
    decoded_token, error = get_user_from_token(request);
    if error: return error
    uid = decoded_token['uid']
    active_statuses = ["accepted", "in_transit", "pickup"]
    tasks_ref = db.collection("p2p_tasks").where(filter=FieldFilter("riderId", "==", uid)).where(filter=FieldFilter("status", "in", active_statuses)).stream()
    active_tasks = [convert_geopoints(task.to_dict()) for task in tasks_ref]
    return jsonify({"tasks": active_tasks}), 200

@app.route("/api/tasks/accept-offer", methods=["POST"])
def accept_task_offer():
    decoded_token, error = get_user_from_token(request);
    if error: return error
    uid = decoded_token['uid']; data = request.get_json(); task_id = data.get("taskId")
    if not task_id: return jsonify({"error": "Missing taskId"}), 400
    task_ref = db.collection("p2p_tasks").document(task_id); task_doc = task_ref.get()
    if not task_doc.exists: return jsonify({"error": "Task not found"}), 404
    task_data = task_doc.to_dict()
    if task_data.get("riderId") != uid: return jsonify({"error": "Not authorized to accept this task"}), 403
    if task_data.get("status") != "pending_acceptance": return jsonify({"error": "This task is no longer available"}), 400
    task_ref.update({"status": "accepted"})
    return jsonify({"status": "success", "message": "Task accepted successfully"}), 200

@app.route("/api/tasks/history", methods=["GET"])
def get_task_history():
    decoded_token, error = get_user_from_token(request);
    if error: return error
    uid = decoded_token['uid']
    terminal_statuses = ["delivered", "cancelled"]
    sent_q = db.collection("p2p_tasks").where(filter=FieldFilter("senderId", "==", uid)).where(filter=FieldFilter("status", "in", terminal_statuses)).stream()
    delivered_q = db.collection("p2p_tasks").where(filter=FieldFilter("riderId", "==", uid)).where(filter=FieldFilter("status", "in", terminal_statuses)).stream()
    tasks, task_ids = [], set()
    def process_task(task_doc):
        task_data = convert_geopoints(task_doc.to_dict())
        if task_data.get('taskId') not in task_ids:
            tasks.append(task_data)
            task_ids.add(task_data.get('taskId'))
    for task in sent_q: process_task(task)
    for task in delivered_q: process_task(task)
    return jsonify({"tasks": tasks}), 200

@app.route("/api/tasks/update-rider-location", methods=["POST"])
def update_rider_location():
    decoded_token, error = get_user_from_token(request);
    if error: return error
    uid = decoded_token['uid']; data = request.get_json()
    task_id, location = data.get("taskId"), data.get("location")
    if not task_id or not location: return jsonify({"error": "Missing taskId or location"}), 400
    task_ref = db.collection("p2p_tasks").document(task_id)
    task_ref.update({"riderLocation": firestore.GeoPoint(location['lat'], location['lng'])})
    return jsonify({"status": "ok"}), 200

@app.route("/api/rate-user", methods=["POST"])
def rate_user():
    decoded_token, error = get_user_from_token(request);
    if error: return error
    uid = decoded_token['uid']; data = request.get_json(); task_id, rating = data.get("taskId"), data.get("rating")
    if not task_id or not rating or not (1 <= rating <= 5): return jsonify({"error": "Missing or invalid fields"}), 400
    task_ref = db.collection("p2p_tasks").document(task_id); task_doc = task_ref.get()
    if not task_doc.exists: return jsonify({"error": "Task not found"}), 404
    task_data = task_doc.to_dict()
    target_user_id = task_data.get("riderId") if uid == task_data.get("senderId") else task_data.get("senderId")
    if not target_user_id: return jsonify({"error": "Cannot rate this user"}), 400
    user_ref = db.collection("users").document(target_user_id)
    @firestore.transactional
    def update_in_transaction(transaction, ref, rating_to_add):
        snapshot = ref.get(transaction=transaction)
        old_rating = snapshot.get("rating", 0); old_count = snapshot.get("ratingCount", 0)
        new_count = old_count + 1
        new_rating = ((old_rating * old_count) + rating_to_add) / new_count
        transaction.update(ref, {"rating": new_rating, "ratingCount": new_count})
    transaction = db.transaction()
    update_in_transaction(transaction, user_ref, rating)
    return jsonify({"status": "success", "message": "Feedback submitted successfully"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
