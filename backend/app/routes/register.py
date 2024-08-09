from flask import Blueprint, request, jsonify
from app import db
from app.models import Account, Company, Profile

# Blueprintの作成
register_bp = Blueprint("register", __name__)


@register_bp.route("/register_company", methods=["POST"])
def register_company():
    data = request.get_json()

    # 必要なデータが提供されているかチェック
    if not all(
        key in data
        for key in ("user_id", "password", "company_name", "industry", "details")
    ):
        return jsonify({"message": "Missing required fields"}), 400

    # アカウントと企業の登録
    try:
        # 企業アカウントをデータベースに追加
        account = Account(
            user_id=data["user_id"], password=data["password"], student=False
        )
        company = Company(
            id=data["user_id"],  # ここでは user_id を企業IDとして使用
            name=data["company_name"],
            industory=data["industry"],
            details=data["details"],
        )
        db.session.add(account)
        db.session.add(company)
        db.session.commit()

        return jsonify({"message": "Company registered successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500


@register_bp.route("/register_student", methods=["POST"])
def register_student():
    data = request.get_json()

    # 必要なデータが提供されているかチェック
    if not all(
        key in data
        for key in (
            "user_id",
            "password",
            "name",
            "university",
            "grade",
            "industory",
            "twitter_account",
        )
    ):
        return jsonify({"message": "Missing required fields"}), 400

    # アカウントと学生のプロフィールを登録
    try:
        # 学生アカウントをデータベースに追加
        account = Account(
            user_id=data["user_id"], password=data["password"], student=True
        )
        # 学生のプロフィールをデータベースに追加
        profile = Profile(
            id=data["user_id"],  # ここでは user_id を学生IDとして使用
            name=data["name"],
            university=data["university"],
            grade=data["grade"],
            industory=data["industory"],
            twitter_account=data["twitter_account"],
        )
        db.session.add(account)
        db.session.add(profile)
        db.session.commit()

        return jsonify({"message": "Student registered successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500
