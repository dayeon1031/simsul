from flask import Flask, render_template, request, redirect, url_for, session
import os
from datetime import datetime
import cv2
import numpy as np
import tensorrt as trt
import pycuda.driver as cuda
import pycuda.autoinit

# Flask 애플리케이션 초기화
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 세션을 사용하기 위한 비밀 키 설정

# 파일 저장 경로 설정
UPLOAD_FOLDER = 'static/images/saved_photos'  # 업로드된 사진을 저장할 폴더
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # 폴더가 없으면 생성

# 일기 저장 파일 설정
DIARY_FILE = 'diaries.txt'  # 일기를 저장할 텍스트 파일

# TensorRT 모델 로드
TRT_LOGGER = trt.Logger(trt.Logger.WARNING)
ENGINE_PATH = 'path_to_your_model.trt'  # TensorRT 엔진 파일 경로

# TensorRT 엔진 로드
def load_engine(engine_path):
    with open(engine_path, 'rb') as f, trt.Runtime(TRT_LOGGER) as runtime:
        return runtime.deserialize_cuda_engine(f.read())

engine = load_engine(ENGINE_PATH)
context = engine.create_execution_context()

# TensorRT 관련 설정
input_binding_idx = engine.get_binding_index('input_0')
output_binding_idx = engine.get_binding_index('output_0')

emotion_labels = ['angry', 'disgust', 'fear', 'happy', 'neutral', 'sad', 'surprise']

# 레이블 매핑
custom_labels = {
    'angry': "화남",
    'disgust': "화남",
    'fear': "당황",
    'happy': "기쁨",
    'neutral': "기쁨",
    'sad': "슬픔",
    'surprise': "당황"
}

# TensorRT 추론 함수
def infer_with_tensorrt(image):
    # 입력 데이터 크기와 출력 데이터 크기 가져오기
    input_shape = engine.get_binding_shape(input_binding_idx)
    output_shape = engine.get_binding_shape(output_binding_idx)

    # 입력 데이터 할당
    input_data = np.ascontiguousarray(image.astype(np.float32).ravel())
    output_data = np.empty(output_shape, dtype=np.float32)

    # GPU 메모리 할당
    d_input = cuda.mem_alloc(input_data.nbytes)
    d_output = cuda.mem_alloc(output_data.nbytes)

    # GPU 메모리에 데이터 복사
    cuda.memcpy_htod(d_input, input_data)

    # 추론 실행
    context.execute_v2([int(d_input), int(d_output)])

    # GPU 메모리에서 결과 복사
    cuda.memcpy_dtoh(output_data, d_output)

    return output_data

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
    if 'photo' not in request.files or request.files['photo'].filename == '':
        print("No photo uploaded!")
        return "No photo uploaded!", 400

    photo = request.files['photo']
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    try:
        photo.save(filepath)
        print(f"Photo saved at: {filepath}")
    except Exception as e:
        print(f"Failed to save photo: {e}")
        return "Failed to save photo!", 500

    # 이미지를 TensorRT 모델 입력 형식으로 전처리
    try:
        img = cv2.imread(filepath)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  # 흑백으로 변환
        img = cv2.resize(img, (48, 48))  # 모델 입력 크기에 맞게 조정
        img = img / 255.0  # 정규화
        img = np.expand_dims(img, axis=(0, 1))  # 배치 차원과 채널 차원 추가

        # TensorRT 모델로 감정 예측
        predictions = infer_with_tensorrt(img)
        emotion_index = np.argmax(predictions)  # 가장 높은 확률의 감정 인덱스
        original_emotion = emotion_labels[emotion_index]  # 원래 레이블
        emotion = custom_labels[original_emotion]  # 사용자 정의 레이블로 매핑
    except Exception as e:
        print(f"Emotion prediction failed: {e}")
        emotion = "알 수 없음"

    session['last_emotion'] = emotion
    print(f"Predicted emotion: {emotion}")

    return render_template('save.html', filename=filename, emotion=emotion)

# 오늘의 일기 작성
@app.route('/today', methods=['GET', 'POST'])
def today():
    if request.method == 'POST':
        diary_text = request.form.get('diary')
        emoji = request.form.get('emoji', session.get('last_emotion', 'default.png'))
        date = datetime.now().strftime('%Y-%m-%d')

        with open(DIARY_FILE, 'a') as f:
            f.write(f"{date} - {emoji}: {diary_text}\n")

        return redirect(url_for('list_diary'))

    emoji = session.get('last_emotion', 'default.png')
    return render_template('today.html', emoji=emoji)

# 일기 목록
@app.route('/list')
def list_diary():
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
    return render_template('game.html')

# 애플리케이션 실행
if __name__ == '__main__':
    app.run(debug=True)
