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
            "grade": "学部3",
            "industry": "IT",
            "twitter_account": "@daigaku_saikou",
            "summary": "サッカーが好きな学生です。海外に行くことが好きで、英語が得意です。",
            "image": "https://as2.ftcdn.net/v2/jpg/08/14/62/33/1000_F_814623317_VHpdjqAUzqxM6v86KsQhi7xa2aEVAHVG.jpg",
            "match": "0%",
            "reason": "",
        },
        {
            "name": "山田花子",
            "university": "東京わんこ大好き大学",
            "grade": "修士1",
            "industry": "飲食",
            "twitter_account": "@wanko_lover",
            "summary": "少し怠惰な面があり、自分に甘いです。協調性は高く、人に好かれているので、友達が多いです。",
            "image": "https://as2.ftcdn.net/v2/jpg/07/68/95/75/1000_F_768957537_8Jk8wDHo9pzEknXBC9mmuUBCRSdon1TX.jpg",
            "match": "0%",
            "reason": "",
        },
        {
            "name": "田中哲平",
            "university": "デジタルボリウッド大学",
            "grade": "修士1",
            "industry": "IT",
            "twitter_account": "@consultant_jiro",
            "summary": "普段からエンジニアとして研鑽を怠らず、ベストを尽くします。自分の理想に向かって突き進みます。普段はエンジニアとしてインターンをしており、他のエンジニアとのコミュニケーションを大切にしています。",
            "image": "https://as2.ftcdn.net/v2/jpg/07/68/95/75/1000_F_768957539_6BLIzLFo0ytpuYEnT4pQxk95GW0f4Psr.jpg",
            "match": "0%",
            "reason": "",
        },
        {
            "name": "山田次郎",
            "university": "イーストキャピタル大学",
            "grade": "学部3",
            "industry": "コンサル",
            "twitter_account": "@consultant_jiro",
            "summary": "性格/n前向きで親しみやすい: 結婚や日常の出来事を喜んで共有し、ポジティブな姿勢を見せています。お祝いに対して感謝の気持ちを示し、結婚祝いのリストも公開するなど、オープンでフレンドリーな一面が見えます。/n社交的: 友人やフォロワーとの交流を大切にし、日常生活や特別な出来事を積極的にシェアしています。/n実直で細かい: 日々の出来事を詳細に報告し、誠実な対応をしている印象があります。/n活動/n学術活動: NAIST渡辺研の博士課程に在籍しており、学位取得に向けて努力しています。言語処理学会の若手支援事業に関与し、関連イベントにも参加しています。/n個人的な生活: 結婚し、家庭を築くことを大切にしており、結婚関連の情報や祝いのリストを公開するなど、プライベートな部分も積極的に共有しています。/n旅行や日常の出来事: 旅行や外出に関する情報も共有し、特に旅行先での経験を詳細に報告しています（例: ホテルチェックインやバス乗り場の情報など）。",
            "image": "https://as2.ftcdn.net/v2/jpg/07/68/95/75/1000_F_768957539_6BLIzLFo0ytpuYEnT4pQxk95GW0f4Psr.jpg",
            "match": "0%",
            "reason": "",
        },
    ]

    for student in student_data:
        match_rate, reason = get_match_rate(student["summary"], student["industry"])
        student["match"] = match_rate
        student["reason"] = reason

    return render_template("student_list.html", student_data=student_data)


def get_match_rate(summary, industory):
    our_culture = "私たちの使命新しい当たり前を作り続ける新しい当たり前を作り続けるVision私たちの目指すべき姿世界一の企業へ世界一の企業へValues私たちの共有価値観やりたいことをできているか？やりたいことをできているか？やっていることは興味があることなのか自己学習したくなるほどか仕事が待ち遠しいと感じたことはあるか仕事をしていてワクワクするか仕事を通して自身の成長を感じられるかやるべきことをしているか？やるべきことをしているか？仕事仲間から必要とされているか問題解決となることに取り組んでいるか事業としてスケールする仕事をしているか今できることより一歩上の目標にトライしているか今すべきことを行っているかいい仲間に囲まれているか？いい仲間に囲まれているか？尊敬できる仲間か困っていたら助けたいと思う仲間と仕事をしているか頼りになると思える仲間がいるか一緒に仕事をしていて楽しいと思える仲間か相談できる仲間がいるかたいせつな人をたいせつにできているか？たいせつな人をたいせつにできているか？たいせつな人に喜ばれているかたいせつな人と一緒にいる時間を確保できているかたいせつな人ときちんと会話をしているかたいせつな人が充実した日々をおくれているか笑顔で過ごせているかベストを尽くしているか？ベストを尽くしているか？どんな状況でも最後まで諦めていないか最善の方法をつねに考え抜いているか細部にまでこだわって仕事をできているか上記のことを行動し続けているか未来を見据えて仕事をしているか"

    msg = [
        {
            "role": "user",
            "content": ""
            + summary
            + "\nこの学生が私たちレアゾンの企業文化に合うかどうかを判定してください。以下がレアゾンの企業の文化です。json形式で、match_rate(int)とreason(string)を返してください。match_rateには0から100までの整数が入ります。match_rateが高い場合はその学生が合う理由を、低い場合はその学生が合わない理由を教えてください。業界とスキルと人間性がマッチするなら90%以上にして"
            + our_culture
            + f"私たちの企業名はレアゾンというIT企業です。学生の志望業界は{industory}です。",
        }
    ]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=msg,
        response_format={"type": "json_object"},
    )
    decoded_json = json.loads(response.choices[0].message.content)
    return decoded_json["match_rate"], decoded_json["reason"]


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
