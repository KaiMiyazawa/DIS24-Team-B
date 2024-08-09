from flask import Blueprint, request, jsonify
from app import db
from app.models import Tweet

tweet_bp = Blueprint("tweet", __name__)


@tweet_bp.route("/delete_tweet", methods=["POST"])
def delete_tweet():
    data = request.get_json()
    tweet = Tweet.query.get(data["id"])

    if tweet:
        db.session.delete(tweet)
        db.session.commit()
        return jsonify({"message": "Tweet deleted"})
    return jsonify({"message": "Tweet not found"}), 404


@tweet_bp.route("/get_tweets_to_delete", methods=["GET"])
def get_tweets_to_delete():
    tweets = Tweet.query.filter_by(should_delete=True).all()
    return jsonify(
        [{"id": t.id, "text": t.text, "date": t.date, "likes": t.likes} for t in tweets]
    )
