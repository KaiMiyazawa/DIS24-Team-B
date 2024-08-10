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

        return redirect(url_for("before_delete"))
    return render_template("Xlogin.html", form=form)


# tweets.db memo
# id, text, date, likes, should_delete, user_id, score,


@app.route("/before_delete/")
def before_delete():
    db_before = sqlite3.connect("data/tweets.db")
    cursor = db_before.cursor()
    cursor.execute("SELECT text, user_id FROM tweets")
    tweets = cursor.fetchall()
    db_before.close()

    db = sqlite3.connect("data/tweets.db")
    cursor = db.cursor()
    score_list = []
    for tweet in tweets:
        print(tweet)
        cursor.execute("UPDATE tweets SET should_delete = 0 WHERE id = ?", (tweet[0],))
    db.commit()
    for tweet in tweets:
        if tweet[1] != 101:
            continue
        res = ""
        while res not in ["1", "2", "3", "4", "5"]:
            msg = [
                {
                    "role": "user",
                    "content": 'This is about tweets \n"'
                    + tweet[0]
                    + '"\n\n これらのツイートの文章はどれくらい適切/ポジティブですか?\n Just awnser "1" to "5". You must not provide any other information. here, "1" means that the tweet is very inappropriate/negative, "2" means that the tweet is inappropriate/negative, "3" means that the tweet is neutral, "4" means that the tweet is appropriate/positive, "5" means that the tweet is very appropriate/positive. You must not provide any other information.',
                }
            ]
            response = client.chat.completions.create(model="gpt-4o-mini", messages=msg)
            res = response.choices[0].message.content
            print("tweet", tweet)
            print("res", res)
        print(response.choices[0].message.content)
        score_list.append(response.choices[0].message.content)
        cursor.execute(
            "UPDATE tweets SET score = ? WHERE text = ?", (int(res), tweet[0])
        )

    db.commit()
    db.close()
    score_list = [int(score) for score in score_list]
    total_score = sum(score_list) / len(score_list)
    total_score = total_score * 200
    # 　切り捨て
    total_score = int(total_score)
    total_score = total_score / 10
    # total_score = round(total_score, 2)
    print("=== Total score ===")
    print(total_score)
    return render_template("before_delete.html", total_score=total_score)


@app.route("/after_delete/")
def after_delete():
    db_after = sqlite3.connect("data/tweets.db")
    cursor = db_after.cursor()
    cursor.execute("SELECT text, should_delete, user_id, score FROM tweets")
    tweets = cursor.fetchall()
    db_after.close()

    score_list = []
    for tweet in tweets:
        print(tweet)
    for tweet in tweets:
        if tweet[2] != 101:
            continue
        if tweet[1] == 0:
            score_list.append(tweet[3])

    # score_list = [int(score) for score in score_list]
    total_score = sum(score_list) / len(score_list)
    total_score = total_score * 200
    # 　切り捨て
    total_score = int(total_score)
    total_score = total_score / 10
    # total_score = round(total_score, 2)
    print("=== Total score ===")
    print(total_score)
    return render_template("after_delete.html", total_score=total_score)


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
        if tweet[5] != 101:
            continue
        if is_inappropriate(tweet):
            inappropriate_list.append(tweet)

    print("=== Inappropriate tweets ===")
    print(inappropriate_list)

    return render_template("listup.html", inappropriate_list=inappropriate_list)


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

    db = sqlite3.connect("data/tweets.db")
    cursor = db.cursor()
    # ツイートを削除
    tweets = cursor.execute("SELECT * FROM tweets").fetchall()

    for tweet in tweets:
        print(tweet)
        cursor.execute("UPDATE tweets SET should_delete = 0 WHERE id = ?", (tweet[0],))
    db.commit()
    tweets = cursor.execute("SELECT * FROM tweets").fetchall()
    print("=== before delete ===")
    print(tweets)
    db.close()

    db = sqlite3.connect("data/tweets.db")
    cursor = db.cursor()
    for tweet_id in request.form.getlist("delete"):
        delete_tweet(tweet_id)
        # データベースの中身を変更
        # sould_delete カラムについて、inappropriate_listに含まれるツイートのidに対して、1をセットする
        cursor.execute("UPDATE tweets SET should_delete = 1 WHERE id = ?", (tweet_id,))
    db.commit()
    tweets = cursor.execute("SELECT * FROM tweets").fetchall()
    print("=== after delete ===")
    print(tweets)
    db.close()

    # 3秒後にリストアップページにリダイレクト
    # ３秒まつ?
    # time.sleep(3)

    return redirect(url_for("after_delete"))


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

    # print(scouts_list)

    # マッチ度と理由のカラムをdbに追加 ======
    scouts_list_copy = scouts_list.copy()
    scouts_list_copy = [list(scout) for scout in scouts_list_copy]
    for scout in scouts_list_copy:
        scout[7] = 0
        scout[8] = ""
    scouts_list_copy = sort_scouts(scouts_list_copy)

    scout_db = sqlite3.connect("data/scouts.db")
    cursor = scout_db.cursor()
    cursor.execute("DELETE FROM scouts")
    for scout in scouts_list_copy:
        cursor.execute(
            "INSERT INTO scouts (id, name, date, industry, details, photo, culture, match_rate, reason) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
            scout,
        )
    scout_db.commit()
    scout_db.close()
    # ========================================

    print("=== Scouts list ===")
    # print(scouts_list)
    return render_template("mypage.html", user="user", scouts_list=scouts_list_copy)


@app.route("/student_list/")
def student_list():
    student_data = [
        {
            "name": "山田太郎",
            "university": "国際サッカー大学",
            "grade": "学部3",
            "industry": "IT",
            "twitter_account": "@daigaku_saikou",
            "summary": "この学生は、サッカーと英語学習に情熱を注いでいるアクティブな人物です。チームプレーの重要性を理解し、連携を重視している一方で、サッカーの練習がハードで体力的な限界を感じることもあるようです。また、異文化に触れることで楽しみを感じており、英語のスキル向上にも積極的です。英語の発音に不安を抱えつつも、学びを続け、海外のニュースもスムーズに読めるようになったことを喜んでいます。試合の結果に一喜一憂しつつも、チームの成長を実感し、次の試合への期待を持っています。",
            "image": "https://as2.ftcdn.net/v2/jpg/08/14/62/33/1000_F_814623317_VHpdjqAUzqxM6v86KsQhi7xa2aEVAHVG.jpg",
            "match": "0%",
            "reason": "",
        },
        {
            "name": "犬山花子",
            "university": "東京わんこ大好き大学",
            "grade": "修士1",
            "industry": "飲食",
            "twitter_account": "@wanko_lover",
            "summary": "この学生は、友人との時間を大切にし、社交的で楽しいことを優先する傾向がある一方で、自己管理や時間管理が苦手で、やる気が出ない日が多いようです。甘やかすことも大切にしつつ、友達への感謝の気持ちも持っているが、時折約束を忘れてしまうことがあることが伺えます。また、のんびりしすぎて、重要な準備や食事を怠ることもありますが、それを気にせず楽しむ姿勢を持っています。",
            "image": "https://as2.ftcdn.net/v2/jpg/07/68/95/75/1000_F_768957537_8Jk8wDHo9pzEknXBC9mmuUBCRSdon1TX.jpg",
            "match": "0%",
            "reason": "",
        },
        {
            "name": "田中哲平",
            "university": "デジタルボリウッド大学",
            "grade": "修士1",
            "industry": "IT",
            "twitter_account": "@IT_teppei",
            "summary": "この学生は、技術学習に対する強い意欲と向上心を持ち、自身の成長を重視しています。失敗から学び、集中力を大切にしながら積極的に挑戦しています。また、新しいツールや技術に対して柔軟に取り組む姿勢があり、困難に直面しても前向きに乗り越えようとしています。目標に向かって全力で努力し、自分の成長が会社に貢献することを信じて日々励んでいます。",
            "image": "https://as2.ftcdn.net/v2/jpg/07/68/95/75/1000_F_768957539_6BLIzLFo0ytpuYEnT4pQxk95GW0f4Psr.jpg",
            "match": "0%",
            "reason": "",
        },
        {
            "name": "浜田孝太郎",
            "university": "イーストキャピタル大学",
            "grade": "学部3",
            "industry": "コンサル",
            "twitter_account": "@consultant_kotaro",
            "summary": "この学生は結婚したばかりで、結婚生活を楽しみながらもさまざまな挑戦に取り組んでいます。イベントへの参加や友人との交流を大切にし、研究活動やプロジェクトにも真剣に取り組んでいます。また、周囲の人々からのサポートや祝福に感謝の気持ちを示しており、前向きな姿勢が感じられます。全体として、社会的なつながりを重視しつつ、学問に対して情熱を持っている学生と言えます。",
            "image": "https://as2.ftcdn.net/v2/jpg/07/68/95/75/1000_F_768957539_6BLIzLFo0ytpuYEnT4pQxk95GW0f4Psr.jpg",
            "match": "0%",
            "reason": "",
        },
    ]

    # DBからユーザー101,102,103,104のツイートを取得し、要約を作成
    for i, student in enumerate(student_data):
        # student["summary"] = summarize_student(101 + i)
        # print(student["summary"])
        # DBにはすでに要約が保存されていると仮定(登録時に処理を行う)
        pass

    rates_for_students = get_match_rate(student_data)
    for i, student in enumerate(student_data):
        match_rate, reason = (
            rates_for_students[f"match_rate_{i}"],
            rates_for_students[f"reason_{i}"],
        )
        student["match"] = match_rate
        student["reason"] = reason
        print(student)

    return render_template("student_list.html", student_data=student_data)


def sort_scouts(scouts_list):
    personality = "私は「IT業界」に進んでソフトウェアエンジニアとして働き様々な事業に取り組みたいと考える学生です。私は性別や年齢に関係なく仲間と高め合える環境で切磋琢磨し、最高のものを作りたいと考えています。"

    msg_content = ""
    for i, scout in enumerate(scouts_list):
        msg_content += (
            "\n私は以下のような特徴を持っています。/n"
            + personality
            + f"私が次の企業に合うかどうかを判定してください。以下がその企業のカルチャーです。json形式で、match_rate_{i}(int)とreason_{i}(string)を返してください。match_rateには0から100までの整数が入ります。match_rateが高い場合はその学生が合う理由のみを、低い場合はその学生が合わない理由を教えてください。志望業界と人間性が合う場合は90%以上にして、それらが不一致な場合は50%以下にして"
            + scout[3]
            + "この企業の業界は"
            + scout[2]
            + "です。"
            + "この企業の名前は"
            + scout[1]
            + "です。"
        )
    msg_content += "jsonの形式は、{'match_rate_0: int, reason_0: string, match_rate_1: int, reason_1: string,...'}です。マッチ度の理由には、「業界の一致度と、私の性格の一致度の両方から説明して」"
    msg = [
        {
            "role": "user",
            "content": msg_content,
        }
    ]
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=msg,
        response_format={"type": "json_object"},
    )
    print(response.choices[0].message.content)
    decoded_json = json.loads(response.choices[0].message.content)
    for i, scout in enumerate(scouts_list):
        scout[7] = decoded_json[f"match_rate_{i}"]
        scout[8] = decoded_json[f"reason_{i}"]
    scouts_list = sorted(scouts_list, key=lambda x: x[7], reverse=True)
    return scouts_list


def get_match_rate(student_data):
    our_culture = "私たちの使命:「新しい当たり前を作り続ける」Vision(私たちの目指すべき姿):\
    「世界一の企業へ」Values(私たちの共有価値観):「やりたいことをできているか？」やっていることは\
        興味があることなのか自己学習したくなるほどか仕事が待ち遠しいと感じたことはあるか仕事をしていて\
            ワクワクするか仕事を通して自身の成長を感じられるか「やるべきことをしているか？」仕事仲間から\
                必要とされているか問題解決となることに取り組んでいるか事業としてスケールする仕事をしているか\
                    今できることより一歩上の目標にトライしているか今すべきことを行っているか「いい仲間に囲まれているか？」\
                        尊敬できる仲間か困っていたら助けたいと思う仲間と仕事をしているか頼りになると思える仲間がいるか\
                            一緒に仕事をしていて楽しいと思える仲間か相談できる仲間がいるか「たいせつな人をたいせつに\
                                できているか？」たいせつな人に喜ばれているかたいせつな人と一緒にいる時間を確保できているか\
                                    たいせつな人ときちんと会話をしているかたいせつな人が充実した日々をおくれているか笑顔で\
                                        過ごせているかベストを尽くしているか？「ベストを尽くしているか？」\
                                            どんな状況でも最後まで諦めていないか最善の方法をつねに考え抜いているか\
                                                細部にまでこだわって仕事をできているか上記のことを行動し続けているか未来を見据えて仕事をしているか"
    msg_content = ""
    for i, student in enumerate(student_data):
        msg_content += (
            student["summary"]
            + f"\nこの学生が私たちレアゾンの企業文化に合うかどうかを判定してください。以下がレアゾンの企業の文化です。json形式で、match_rate_{i}(int)とreason_{i}(string)を返してください。match_rateには0から100までの整数が入ります。match_rateが高い場合はその学生が合う理由を、低い場合はその学生が合わない理由をレアゾンのカルチャーを引用しつつ教えてください。業界とスキルと人間性がマッチするならマッチ度を90%以上にして"
            + our_culture
            + f"私たちの企業名はレアゾンという、ゲームや広告、フードテックなど幅広い事業を手がけて海外にも拠点を置くIT企業です。学生の志望業界は{student['industry']}です。"
        )

    msg_content += "jsonの形式は、{'match_rate_0: int, reason_0: string, match_rate_1: int, reason_1: string, match_rate_2: int, reason_2: string, match_rate_3: int, reason_3: stringstring'}です。マッチ度の理由には、「学生の志望業界の一致度と、学生の性格とレアゾンのカルチャーの一致度の両方から説明して」"

    msg = [
        {
            "role": "user",
            "content": msg_content,
        }
    ]

    while True:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=msg,
            response_format={"type": "json_object"},
        )
        decoded_json = json.loads(response.choices[0].message.content)

        # Check if all match_rate_i and reason_i are present
        valid_response = True
        for i in range(len(student_data)):
            if (
                f"match_rate_{i}" not in decoded_json
                or f"reason_{i}" not in decoded_json
            ):
                valid_response = False
                break

        if valid_response:
            break
    print(decoded_json)
    print(len(student_data))

    return decoded_json


def summarize_student(id):
    db = sqlite3.connect("data/tweets.db")
    cursor = db.cursor()
    cursor.execute(
        f"SELECT text FROM tweets WHERE user_id = {id} and should_delete = 0"
    )
    tweets = cursor.fetchall()
    print(tweets)
    tweets = "".join([tweet[0] for tweet in tweets])
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
