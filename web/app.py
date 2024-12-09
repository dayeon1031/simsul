from flask import Flask, render_template, request, redirect, url_for, session
import os
import random
from datetime import datetime
from keras.models import load_model
import cv2
import numpy as np

# Flask 애플리케이션 초기화
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 세션을 사용하기 위한 비밀 키 설정

# 파일 저장 경로 설정
UPLOAD_FOLDER = 'static/images/saved_photos'  # 업로드된 사진을 저장할 폴더
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # 폴더가 없으면 생성

# 일기 저장 파일 설정
DIARY_FILE = 'diaries.txt'  # 일기를 저장할 텍스트 파일

# RT 모델 로드
MODEL_PATH = 'path_to_your_model.h5'  # 모델 파일 경로
model = load_model(MODEL_PATH)

# 표정 레이블 정의
expressions = ["화남", "당황", "기쁨", "슬픔"]

# 루트 경로로 접근 시 /start로 리다이렉트
@app.route('/')
def redirect_to_start():
    return redirect(url_for('start'))

# 시작 화면
@app.route('/start')
def start():
    return render_template('start.html')

# 메인 화면
@app.route('/index')
def index():
    return render_template('index.html')

# 사진 업로드 및 저장
@app.route('/save', methods=['POST'])
def save():
    # 업로드된 파일 확인
    if 'photo' not in request.files or request.files['photo'].filename == '':
        print("No photo uploaded!")
        return "No photo uploaded!", 400  # 업로드된 파일이 없으면 에러 반환

    photo = request.files['photo']  # 업로드된 파일 가져오기
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"  # 파일 이름에 시간 추가
    filepath = os.path.join(UPLOAD_FOLDER, filename)  # 저장 경로 설정

    try:
        photo.save(filepath)  # 파일 저장
        print(f"Photo saved at: {filepath}")
    except Exception as e:
        print(f"Failed to save photo: {e}")
        return "Failed to save photo!", 500  # 저장 실패 시 에러 반환

    # 이미지를 RT 모델 입력 형식으로 전처리
    try:
        img = cv2.imread(filepath)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, (48, 48))  # 모델 입력 크기에 맞게 조정
        img = img / 255.0  # 정규화
        img = np.expand_dims(img, axis=0)  # 배치 차원 추가

        # 모델을 사용하여 감정 예측
        predictions = model.predict(img)
        emotion_index = np.argmax(predictions)  # 가장 높은 확률의 감정 인덱스
        emotion = expressions[emotion_index]
    except Exception as e:
        print(f"Emotion prediction failed: {e}")
        emotion = "알 수 없음"  # 예측 실패 시 기본값

    session['last_emotion'] = emotion  # 세션에 표정 저장
    print(f"Predicted emotion: {emotion}")

    return render_template('save.html', filename=filename, emotion=emotion)

# 오늘의 일기 작성
@app.route('/today', methods=['GET', 'POST'])
def today():
    if request.method == 'POST':  # POST 요청으로 일기 저장
        diary_text = request.form.get('diary')  # 일기 내용 가져오기
        emoji = request.form.get('emoji', session.get('last_emotion', 'default.png'))  # 표정 가져오기
        date = datetime.now().strftime('%Y-%m-%d')  # 오늘 날짜

        with open(DIARY_FILE, 'a') as f:  # 일기를 파일에 추가
            f.write(f"{date} - {emoji}: {diary_text}\n")

        return redirect(url_for('list_diary'))  # 일기 목록으로 리다이렉트

    emoji = session.get('last_emotion', 'default.png')  # 세션에서 마지막 감정 가져오기
    return render_template('today.html', emoji=emoji)  # 일기 작성 화면 렌더링

# 일기 목록
@app.route('/list')
def list_diary():
    diaries = []  # 일기 목록 초기화
    if os.path.exists(DIARY_FILE):  # 일기 파일 존재 여부 확인
        with open(DIARY_FILE, 'r') as f:
            diaries = f.readlines()  # 파일에서 일기 읽기

        # 일기가 10개를 초과하면 오래된 일기 삭제
        if len(diaries) > 10:
            diaries = diaries[-10:]  # 최근 10개만 유지
            with open(DIARY_FILE, 'w') as f:
                f.writelines(diaries)  # 수정된 일기 목록 저장

    return render_template('list.html', diaries=diaries)  # 일기 목록 화면 렌더링

# 게임 화면
@app.route('/game')
def game():
    return render_template('game.html')

# 애플리케이션 실행
if __name__ == '__main__':
    app.run(debug=True)  # 디버그 모드로 실행
