from flask import Blueprint, request, jsonify
from app import db
from app.models import Profile
from uuid import uuid4

profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/create_profile", methods=["POST"])
def create_profile():
    data = request.get_json()
    id = str(uuid4())

    profile = Profile(
        id=id,
        name=data["name"],
        university=data["university"],
        grade=data["grade"],
        industory=data["industory"],
        twitter_account=data["twitter_account"],
    )
    db.session.add(profile)
    db.session.commit()
    return jsonify({"message": "Profile created"})


@profile_bp.route("/get_students", methods=["GET"])
def get_students():
    profiles = Profile.query.all()
    return jsonify(
        [
            {
                "id": p.id,
                "name": p.name,
                "university": p.university,
                "grade": p.grade,
                "industory": p.industory,
                "twitter_account": p.twitter_account,
            }
            for p in profiles
        ]
    )
