from app import create_app
from flask import Flask
from flask import jsonify
from openai import OpenAI
import json

# app = create_app()
app = Flask(__name__)

with open("api_key", "r") as file:
    api_key = file.read().strip()

client = OpenAI(api_key=api_key)


@app.route("/fetch_tweets")
def fetch_tweets():
    data = [
        {
            "user_id": "@daigaku_saikou",
            "text": "I love my university!",
            "date": "2021-01-01",
            "likes": 100,
            "id": 1,
        },
        {
            "user_id": "@daigaku_saikou",
            "text": "教授うぜー!",
            "date": "2021-01-01",
            "likes": 100,
            "id": 2,
        },
    ]
    return jsonify(data)


@app.route("/filter_tweets")
def filter_tweets():
    data = [
        {
            "user_id": "@daigaku_saikou",
            "text": "I love my university!",
            "date": "2021-01-01",
            "likes": 100,
            "id": 1,
        },
        {
            "user_id": "@daigaku_saikou",
            "text": "教授うぜー!",
            "date": "2021-01-01",
            "likes": 100,
            "id": 2,
        },
    ]

    to_be_filtered = []
    for tweet in data:

        MODEL = "gpt-4o-mini"
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "あなたは与えられた文章が人々を不快な気持ちにさせる可能性があるかどうかを判断するAIです。出力はjsonで返して、is_inflammatoryがTrueの場合は不快な文章として。",
                },
                {"role": "user", "content": tweet["text"]},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )

        decoded_json = json.loads(response.choices[0].message.content)
        if decoded_json["is_inflammatory"]:
            to_be_filtered.append(tweet)
    return jsonify(to_be_filtered)


@app.route("/fetch_scouts")
def fetch_scouts():
    data = [
        {
            "company_name": "株式会社最高夢物語",
            "industry": "IT",
            "details": "最高の会社です",
            "date": "2021-01-01",
            "accepted": "yes",
            "rejected": False,
        },
        {
            "company_name": "ワールド牛丼カンパニー",
            "industry": "飲食",
            "details": "私たちと一緒に最高の牛丼を作りましょう",
            "date": "2021-02-02",
            "accepted": "no",
            "rejected": True,
        },
        {
            "company_name": "でっかいビル建てまくり株式会社",
            "industry": "建設",
            "details": "でっかいビルを建てまくります",
            "date": "2021-03-03",
            "accepted": "yes",
            "rejected": False,
        },
    ]

    return jsonify(data)


@app.route("/view_student_profiles")
def view_student_profiles():
    data = [
        {
            "name": "山田太郎",
            "university": "最高大学",
            "grade": 4,
            "industry": "IT",
            "twitter_account": "@daigaku_saikou",
            "summary": "最高の大学生です",
        },
        {
            "name": "山田花子",
            "university": "東京わんこ大好き大学",
            "grade": 4,
            "industry": "飲食",
            "twitter_account": "@wanko_lover",
        },
        {
            "name": "山田次郎",
            "university": "イーストキャピタル大学",
            "grade": 4,
            "industry": "コンサル",
            "twitter_account": "@consultant_jiro",
        },
    ]

    return jsonify(data)


if __name__ == "__main__":
    app.run(debug=True)
