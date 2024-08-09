from flask import Blueprint, request, jsonify
from app import db
from app.models import Account

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    user = Account.query.filter_by(user_id=data["user_id"]).first()

    if user and user.password == data["password"]:
        return jsonify({"message": "Login successful"})
    return jsonify({"message": "Invalid credentials"}), 401
