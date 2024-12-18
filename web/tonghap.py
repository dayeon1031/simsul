import os
import time
import cv2
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
from ultralytics import YOLO

# Flask 애플리케이션 초기화
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 세션을 사용하기 위한 비밀 키 설정

# YOLO 모델 초기화
model = YOLO("best.engine")  # YOLO 모델 파일 경로를 지정하세요

# 파일 저장 경로 설정
UPLOAD_FOLDER = 'static/images/saved_photos'  # 업로드된 사진을 저장할 폴더 경로
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # 폴더가 없으면 생성

# 일기 저장 파일 경로 설정
DIARY_FILE = 'diaries.txt'  # 일기 내용을 저장할 텍스트 파일 이름

# 모델의 원래 레이블 (영어)
emotion_labels = ['angry', 'disgust', 'fear', 'happy', 'neutral', 'sad', 'surprise']

# 사용자 정의 레이블 매핑 (한글)
custom_labels = {
    'angry': "화남",
    'disgust': "역겨움",
    'fear': "당황",
    'happy': "기쁨",
    'neutral': "평범",
    'sad': "슬픔",
    'surprise': "당황"
}
# 얼굴 추출 및 감정 분석
def process_and_predict_emotion(image_path):
    """
    얼굴을 추출한 후 감정을 예측하는 함수
    """
    # Load Haar Cascade for face detection
    face_cascade = cv2.CascadeClassifier('/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml')

    # Read and process the image
    frame = cv2.imread(image_path)
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect faces in the image
    faces = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    if len(faces) == 0:
        raise ValueError("No face detected in the image.")

    # Process the first detected face
    x, y, w, h = faces[0]
    face_region = frame[y:y+h, x:x+w]

    # Save the cropped face image
    face_filename = f"face_{os.path.basename(image_path)}"
    face_image_path = os.path.join(UPLOAD_FOLDER, face_filename)
    cv2.imwrite(face_image_path, face_region)

    # Predict emotion using YOLO model
    results = model.predict(source=face_region, show=False)
    if results[0].boxes:
        class_idx = int(results[0].boxes[0].cls[0])
        emotion = emotion_labels[class_idx]
    else:
        emotion = "Unknown"

    return emotion, face_image_path



# 루트 경로 접근 시 시작 화면으로 리다이렉트
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

# 사진 업로드 및 감정 예측
@app.route('/save', methods=['POST'])
def save():
    """
    업로드된 사진을 저장하고 YOLO 모델로 감정을 예측하여 반환하는 함수
    """
    if 'photo' not in request.files or request.files['photo'].filename == '':
        return "No photo uploaded!", 400

    photo = request.files['photo']  # 업로드된 파일 가져오기
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"  # 저장할 파일 이름 생성
    filepath = os.path.join(UPLOAD_FOLDER, filename)  # 파일 저장 경로 설정

    try:
        photo.save(filepath)  # 파일 저장
    except Exception as e:
        return f"Failed to save photo: {e}", 500

    try:
        # 얼굴만 잘라서 감정 분석
        emotion, face_image_path = process_and_predict_emotion(filepath)
        face_filename = os.path.basename(face_image_path)  # 파일 이름만 추출
        session['last_emotion'] = emotion
    except Exception as e:
        return f"Error processing image: {e}", 500

    return render_template('save.html', filename=face_filename, emotion=emotion)

# 오늘의 일기 작성
@app.route('/today', methods=['GET', 'POST'])
def today():
    """
    오늘의 일기를 작성하고 저장하거나, 작성 화면을 반환하는 함수
    """
    if request.method == 'POST':
        diary_text = request.form.get('diary')  # 사용자가 작성한 일기 내용
        emoji = session.get('last_emotion', 'neutral')  # 세션에서 마지막 감정 (영어 레이블)
        date = datetime.now().strftime('%Y-%m-%d')  # 현재 날짜

        # 다이어리 파일에 영어 감정을 저장
        with open(DIARY_FILE, 'a') as f:
            f.write(f"{date} - {emoji}: {diary_text}\n")

        return redirect(url_for('list_diary'))

    emoji = session.get('last_emotion', 'neutral')  # 기본값을 영어 감정으로 설정
    return render_template('today.html', emoji=emoji)

# 일기 목록
@app.route('/list')
def list_diary():
    """
    저장된 일기 목록을 반환하는 함수
    """
    diaries = []
    if os.path.exists(DIARY_FILE):
        with open(DIARY_FILE, 'r') as f:
            diaries = f.readlines()

        if len(diaries) > 10:
            diaries = diaries[-10:]
            with open(DIARY_FILE, 'w') as f:
                f.writelines(diaries)

    return render_template('list.html', diaries=diaries)

# 게임 화면
@app.route('/game')
def game():
    """
    게임 화면을 반환하는 함수
    """
    return render_template('game.html')

# 표정 평가 엔드포인트
@app.route('/evaluate_expression', methods=['POST'])
def evaluate_expression():
    """
    사용자가 업로드한 사진을 YOLO 모델로 분석하여 표정을 반환하는 엔드포인트
    """
    if 'photo' not in request.files or request.files['photo'].filename == '':
        return {"error": "No photo uploaded!"}, 400

    photo = request.files['photo']
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    try:
        photo.save(filepath)
        # 얼굴만 자르고 감정을 예측
        emotion, face_image_path = process_and_predict_emotion(filepath)
        korean_emotion = custom_labels.get(emotion, "알 수 없음")  # 한글로 변환
    except Exception as e:
        return {"error": str(e)}, 500

    return {"userExpression": korean_emotion, "faceImage": os.path.basename(face_image_path)}, 200

# 애플리케이션 실행
if __name__ == '__main__':
    app.run(debug=True)
