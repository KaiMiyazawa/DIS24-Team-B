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
api_key = 'YOUR_API_KEY'
api_key_secret = 'YOUR_API_KEY_SECRET'
access_token = 'YOUR_ACCESS_TOKEN'
access_token_secret = 'YOUR_ACCESS_TOKEN_SECRET'

# 認証
auth = tweepy.OAuthHandler(api_key, api_key_secret)
auth.set_access_token(access_token, access_token_secret)

# APIオブジェクトの作成
api = tweepy.API(auth)

# ================== OpenAI API ==================

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ================== Flask ==================

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # 実際の使用時は安全な秘密鍵に変更してください


# ログインフォームの作成 ============================

class LoginForm(FlaskForm):
    account_type = RadioField('アカウントタイプ', choices=[('public', 'publicアカウント'), ('private', 'privateアカウント')], default='public')
    username = StringField('ユーザーID', validators=[DataRequired()])
    password = PasswordField('パスワード')
    submit = SubmitField('ログイン')

# ログインページ ====================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        return redirect(url_for('mypage'))
    return render_template('login.html', form=form)

@app.route('/signin/', methods=['GET', 'POST'])
def signin():
    # ユーザー認証を行う関数 ===
    def check_credentials(username, password, account_type):
        if account_type == 'public':
            # Twitter APIを使ってユーザー認証を行います
            # ここでは代わりに簡単な文字列比較を行います
            if username == 'user':
                return True
            else:
                return False
        elif account_type == 'private':
            if username == 'user' and password == 'pass':
                return True
            else:
                return False
        else:
            return False

    form = LoginForm()
    if form.validate_on_submit():
        # X(Twitter)のアカウントかどうかを判定
        # 違ったらエラー

        if check_credentials(form.username.data, form.password.data, form.account_type.data) == False:
            return redirect(url_for('login_error'))

        return redirect(url_for('listup'))
    return render_template('Xlogin.html', form=form)

@app.route('/listup/')
def listup():
    # Twitter APIを使ってツイートを取得、openai APIを使ってツイートの内容を分析、不適切なツイートを一覧し、削除の提案をする
    # ここではTwitter APIを使ってツイートを取得したと仮定します
    # tweets.dbにツイートを保存しておく

    # 不適切なツイートかどうかを判定する関数
    def is_inappropriate(tweet):
        print(tweet)
        # openai APIを使ってツイートの内容を分析
        msg = [{"role": "user", "content": "This is about a tweet" + tweet[1] + "\n\n Is this tweet inappropriate?\n Just awnser \"Yes\" or \"No\". You must not provide any other information. here, \"inappropriate\" means that the tweet contains Discriminatory or offensive content, Violent or extreme content, Misinformation or false rumors, Disclosure of personal information, Harassment or bullying, Defamation or slander, Copyright infringement, Promoting illegal or unethical behavior, Pornographic or adult content. also, if You think the tweet includes negative content, please answer \"Yes\"."}]
        response = client.chat.completions.create(
				model="gpt-3.5-turbo",
				messages=msg
			)
        print(response.choices[0].message.content)
        if response.choices[0].message.content in ["Yes", "yes", "YES", "Y", "y", "Yes.", "yes.", "YES.", "Y.", "y."]:
            return True
        else:
            return False

    # ツイートの内容を分析
    # openai APIを使ってツイートの内容を分析
    db = sqlite3.connect('data/tweets.db')
    cursor = db.cursor()
    cursor.execute('SELECT * FROM tweets')
    tweets = cursor.fetchall()
    db.close()

    inappropriate_list = []
    for tweet in tweets:
        if is_inappropriate(tweet):
            inappropriate_list.append(tweet)

    print("=== Inappropriate tweets ===")
    print(inappropriate_list)

    return render_template('listup.html', inappropriate_list=inappropriate_list)

# listup.html
#<body>
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
#</body>

@app.route('/cleanup/', methods=['POST'])
def cleanup():
    # ツイートを削除する関数
    def delete_tweet(tweet_id):
        print("delete tweet: " + tweet_id)

    # ツイートを削除
    for tweet_id in request.form.getlist('delete'):
        delete_tweet(tweet_id)

    # 3秒後にリストアップページにリダイレクト
    #３秒まつ?
    #time.sleep(3)

    return redirect(url_for('mypage'))


@app.route('/success/')
def success():
    return "ログイン成功！"

@app.route('/login_error/')
def login_error():
    return "ログイン失敗"

@app.route('/mypage/')
def mypage():
    return render_template('mypage.html', user='user')

if __name__ == '__main__':
    app.run(debug=True)

