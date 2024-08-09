from flask import Blueprint, request, jsonify
from app import db
from app.models import Profile
from uuid import uuid4

profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/fetch_tweets", methods=["GET"])
def fetch_tweets():
    data = {
        "user_id": "@daigaku_saikou",
        "text": "I love my university!",
        "date": "2021-01-01",
        "likes": 100,
    }
    print("Fetched tweets")
    return jsonify(data)
