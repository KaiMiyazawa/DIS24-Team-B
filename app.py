from flask import Flask, render_template, request, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, RadioField
from wtforms.validators import DataRequired
import tweepy
import os
import json
import requests
import sqlite3
from openai import OpenAI

# ３秒待つ時のライブラリ
import time

# ================== Twitter API ==================
import tweepy

# APIキーとトークンの設定
api_key = "YOUR_API_KEY"
api_key_secret = "YOUR_API_KEY_SECRET"
access_token = "YOUR_ACCESS_TOKEN"
access_token_secret = "YOUR_ACCESS_TOKEN_SECRET"

# 認証
auth = tweepy.OAuthHandler(api_key, api_key_secret)
auth.set_access_token(access_token, access_token_secret)

# APIオブジェクトの作成
api = tweepy.API(auth)

# ================== OpenAI API ==================

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# ================== Flask ==================

app = Flask(__name__)
app.config["SECRET_KEY"] = (
    "your_secret_key"  # 実際の使用時は安全な秘密鍵に変更してください
)


# ログインフォームの作成 ============================


class LoginForm(FlaskForm):
    account_type = RadioField(
        "アカウントタイプ",
        choices=[("public", "publicアカウント"), ("private", "privateアカウント")],
        default="public",
    )
    username = StringField("ユーザーID", validators=[DataRequired()])
    password = PasswordField("パスワード")
    submit = SubmitField("ログイン")


# 企業ログインフォームの作成 ============================
class CompanyLoginForm(FlaskForm):
    username = StringField("ユーザーID", validators=[DataRequired()])
    password = PasswordField("パスワード")
    submit = SubmitField("ログイン")


# ログインページ ====================================


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login/", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        return redirect(url_for("mypage"))
    return render_template("login.html", form=form)


@app.route("/signin/", methods=["GET", "POST"])
def signin():
    # ユーザー認証を行う関数 ===
    def check_credentials(username, password, account_type):
        if account_type == "public":
            # Twitter APIを使ってユーザー認証を行います
            # ここでは代わりに簡単な文字列比較を行います
            if username == "user":
                return True
            else:
                return False
        elif account_type == "private":
            if username == "user" and password == "pass":
                return True
            else:
                return False
        else:
            return False

    form = LoginForm()
    if form.validate_on_submit():
        # X(Twitter)のアカウントかどうかを判定
        # 違ったらエラー

        if (
            check_credentials(
                form.username.data, form.password.data, form.account_type.data
            )
            == False
        ):
            return redirect(url_for("login_error"))

        return redirect(url_for("listup"))
    return render_template("Xlogin.html", form=form)


@app.route("/listup/")
def listup():
    # Twitter APIを使ってツイートを取得、openai APIを使ってツイートの内容を分析、不適切なツイートを一覧し、削除の提案をする
    # ここではTwitter APIを使ってツイートを取得したと仮定します
    # tweets.dbにツイートを保存しておく

    # 不適切なツイートかどうかを判定する関数
    def is_inappropriate(tweet):
        print(tweet)
        # openai APIを使ってツイートの内容を分析
        msg = [
            {
                "role": "user",
                "content": "This is about a tweet"
                + tweet[1]
                + '\n\n Is this tweet inappropriate?\n Just awnser "Yes" or "No". You must not provide any other information. here, "inappropriate" means that the tweet contains Discriminatory or offensive content, Violent or extreme content, Misinformation or false rumors, Disclosure of personal information, Harassment or bullying, Defamation or slander, Copyright infringement, Promoting illegal or unethical behavior, Pornographic or adult content. also, if You think the tweet includes negative content, please answer "Yes".',
            }
        ]
        response = client.chat.completions.create(model="gpt-4o-mini", messages=msg)
        print(response.choices[0].message.content)
        if response.choices[0].message.content in [
            "Yes",
            "yes",
            "YES",
            "Y",
            "y",
            "Yes.",
            "yes.",
            "YES.",
            "Y.",
            "y.",
        ]:
            return True
        else:
            return False

    # ツイートの内容を分析
    # openai APIを使ってツイートの内容を分析
    db = sqlite3.connect("data/tweets.db")
    cursor = db.cursor()
    cursor.execute("SELECT * FROM tweets")
    tweets = cursor.fetchall()
    db.close()

    inappropriate_list = []
    for tweet in tweets:
        if is_inappropriate(tweet):
            inappropriate_list.append(tweet)

    print("=== Inappropriate tweets ===")
    print(inappropriate_list)

    return render_template("listup.html", inappropriate_list=inappropriate_list)


# listup.html
# <body>
#    <h1>Twitterリストアップ</h1>
#    <form action="/cleanup" method="post">
#        {% if inappropriate_list %}
#            {% for tweet in inappropriate_list %}
#            <div class="tweet">
#                <div class="header">
#                    <input type="checkbox" name="delete" value="{{ tweet[0] }}">
#                    <span>{{ tweet[1] }}</span>
#                </div>
#                <div class="footer">
#                    <span>{{ tweet[2] }}</span>
#                </div>
#            </div>
#            {% endfor %}
#        {% else %}
#            <p>不適切なツイートは見つかりませんでした。</p>
#        {% endif %}
#        <button type="submit">削除</button>
#    </form>
# </body>


@app.route("/company/", methods=["GET", "POST"])
def company_info():
    form = LoginForm()
    if form.validate_on_submit():
        return redirect(url_for("student_list"))
    return render_template("company.html", form=form)


@app.route("/cleanup/", methods=["POST"])
def cleanup():
    # ツイートを削除する関数
    def delete_tweet(tweet_id):
        print("delete tweet: " + tweet_id)

    # ツイートを削除
    for tweet_id in request.form.getlist("delete"):
        delete_tweet(tweet_id)

    # 3秒後にリストアップページにリダイレクト
    # ３秒まつ?
    # time.sleep(3)

    return redirect(url_for("mypage"))


@app.route("/success/")
def success():
    return "ログイン成功！"


@app.route("/login_error/")
def login_error():
    return "ログイン失敗"


@app.route("/mypage/")
# <!-- 企業からきたスカウトの管理画面 -->
# <!-- data/scouts.dbに企業から来たスカウトの情報がある -->
# <!-- scouts.dbのカラム id, name, industry, details, photo -->
def mypage():
    scout_db = sqlite3.connect("data/scouts.db")
    cursor = scout_db.cursor()
    cursor.execute("SELECT * FROM scouts")
    scouts_list = cursor.fetchall()
    scout_db.close()

    print("=== Scouts list ===")
    print(scouts_list)
    return render_template("mypage.html", user="user", scouts_list=scouts_list)


@app.route("/student_list/")
def student_list():
    student_data = [
        {
            "name": "山田太郎",
            "university": "最高大学",
            "grade": 4,
            "industry": "IT",
            "twitter_account": "@daigaku_saikou",
            "summary": "最高の大学生です",
            "image": "https://as2.ftcdn.net/v2/jpg/08/14/62/33/1000_F_814623317_VHpdjqAUzqxM6v86KsQhi7xa2aEVAHVG.jpg",
        },
        {
            "name": "山田花子",
            "university": "東京わんこ大好き大学",
            "grade": 4,
            "industry": "飲食",
            "twitter_account": "@wanko_lover",
            "summary": "わんこが大好きな大学生です",
            "image": "https://as2.ftcdn.net/v2/jpg/07/68/95/75/1000_F_768957537_8Jk8wDHo9pzEknXBC9mmuUBCRSdon1TX.jpg",
        },
        {
            "name": "山田次郎",
            "university": "イーストキャピタル大学",
            "grade": 4,
            "industry": "コンサル",
            "twitter_account": "@consultant_jiro",
            "summary": "コンサルタント志望の大学生です",
            "image": "https://as2.ftcdn.net/v2/jpg/07/68/95/75/1000_F_768957539_6BLIzLFo0ytpuYEnT4pQxk95GW0f4Psr.jpg",
        },
    ]

    student_data[0]["summary"] = summarize_student()
    return render_template("student_list.html", student_data=student_data)


def summarize_student():
    db = sqlite3.connect("data/tweets.db")
    cursor = db.cursor()
    cursor.execute("SELECT * FROM tweets")
    tweets = cursor.fetchall()
    # リストを１つの文字列に変換
    tweets = "\n".join([tweet[1] for tweet in tweets])
    db.close()
    msg = [
        {
            "role": "user",
            "content": ""
            + tweets
            + "学生のこれらのツイートを読んで、この学生の特徴を端的に要約してください。",
        }
    ]
    response = client.chat.completions.create(model="gpt-4o-mini", messages=msg)
    return response.choices[0].message.content


if __name__ == "__main__":
    app.run(debug=True)
