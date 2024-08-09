from flask import Blueprint, request, jsonify
from app import db
from app.models import Scout, Company
from datetime import datetime
import uuid

scout_bp = Blueprint("scout", __name__)


@scout_bp.route("/get_scout_list", methods=["POST"])
def get_scout_list():
    data = request.get_json()
    # ScoutテーブルとCompanyテーブルを結合してクエリを作成
    scouts = (
        db.session.query(Scout, Company)
        .join(Company, Scout.company_id == Company.id)
        .filter(Scout.student_id == data["student_id"], Scout.rejected == False)
        .all()
    )

    # JSON形式に変換して返す
    return jsonify(
        [
            {
                "scout_id": s.id,
                "company_id": c.id,
                "company_name": c.name,
                "industry": c.industory,
                "date": s.date,
                "accepted": s.accepted,
            }
            for s, c in scouts
        ]
    )


@scout_bp.route("/accept_reject_scout", methods=["POST"])
def accept_reject_scout():
    data = request.get_json()
    scout = Scout.query.get(data["id"])

    if scout:
        scout.accepted = data["accepted"]
        scout.rejected = data["rejected"]
        db.session.commit()
        return jsonify({"message": "Scout updated"})
    return jsonify({"message": "Scout not found"}), 404


@scout_bp.route("/send_scout", methods=["POST"])
def send_scout():
    data = request.get_json()
    date = datetime.strptime(data["date"], "%Y-%m-%d").date()
    # uuidでidを生成
    id = str(uuid.uuid4())
    scout = Scout(
        id=id,
        company_id=data["company_id"],
        student_id=data["student_id"],
        date=date,
        accepted="pending",
        rejected=False,
    )
    db.session.add(scout)
    db.session.commit()
    return jsonify({"message": "Scout sent"})
