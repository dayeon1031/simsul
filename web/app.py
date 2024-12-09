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
UPLOAD_FOLDER = 'static/images/saved_photos'  # 업로드된 사진을 저장할 폴더 경로
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # 폴더가 없으면 생성

# 일기 저장 파일 경로 설정
DIARY_FILE = 'diaries.txt'  # 일기 내용을 저장할 텍스트 파일 이름

# TensorRT 로깅 및 모델 경로
TRT_LOGGER = trt.Logger(trt.Logger.WARNING)  # TensorRT 로깅 설정
ENGINE_PATH = 'path_to_your_model.trt'  # TensorRT 엔진 파일 경로

# TensorRT 엔진 로드 함수
def load_engine(engine_path):
    """
    TensorRT 엔진을 파일에서 로드하여 반환하는 함수
    """
    with open(engine_path, 'rb') as f, trt.Runtime(TRT_LOGGER) as runtime:
        return runtime.deserialize_cuda_engine(f.read())

# TensorRT 엔진 및 실행 컨텍스트 생성
engine = load_engine(ENGINE_PATH)
context = engine.create_execution_context()

# TensorRT 모델 입력 및 출력 바인딩 인덱스 설정
input_binding_idx = engine.get_binding_index('input_0')  # 입력 데이터의 바인딩 인덱스
output_binding_idx = engine.get_binding_index('output_0')  # 출력 데이터의 바인딩 인덱스

# 모델의 원래 레이블 (영어)
emotion_labels = ['angry', 'disgust', 'fear', 'happy', 'neutral', 'sad', 'surprise']

# 사용자 정의 레이블 매핑 (한글)
custom_labels = {
    'angry': "화남",
    'disgust': "화남",  # 'angry'와 'disgust'를 "화남"으로 통합
    'fear': "당황",
    'happy': "기쁨",
    'neutral': "평범",  # 'neutral'을 "평범" 으로 매핑
    'sad': "슬픔",
    'surprise': "당황"  # 'surprise'를 "당황"으로 매핑
}

# TensorRT 추론 함수
def infer_with_tensorrt(image):
    """
    이미지를 TensorRT 모델에 입력하여 추론 결과를 반환하는 함수
    """
    # 입력 및 출력 데이터 크기 가져오기
    input_shape = engine.get_binding_shape(input_binding_idx)
    output_shape = engine.get_binding_shape(output_binding_idx)

    # 입력 데이터를 연속 배열로 변환
    input_data = np.ascontiguousarray(image.astype(np.float32).ravel())
    output_data = np.empty(output_shape, dtype=np.float32)  # 출력 데이터 공간 확보

    # GPU 메모리 할당
    d_input = cuda.mem_alloc(input_data.nbytes)  # 입력 데이터 크기만큼 GPU 메모리 할당
    d_output = cuda.mem_alloc(output_data.nbytes)  # 출력 데이터 크기만큼 GPU 메모리 할당

    # GPU 메모리에 데이터 복사
    cuda.memcpy_htod(d_input, input_data)

    # 추론 실행
    context.execute_v2([int(d_input), int(d_output)])

    # GPU 메모리에서 결과 데이터 복사
    cuda.memcpy_dtoh(output_data, d_output)

    return output_data  # 추론 결과 반환

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
    업로드된 사진을 저장하고 TensorRT 모델로 감정을 예측하여 반환하는 함수
    """
    # 업로드된 파일이 없는 경우 에러 반환
    if 'photo' not in request.files or request.files['photo'].filename == '':
        print("No photo uploaded!")
        return "No photo uploaded!", 400

    photo = request.files['photo']  # 업로드된 파일 가져오기
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"  # 저장할 파일 이름 생성
    filepath = os.path.join(UPLOAD_FOLDER, filename)  # 파일 저장 경로 설정

    try:
        photo.save(filepath)  # 파일 저장
        print(f"Photo saved at: {filepath}")
    except Exception as e:
        print(f"Failed to save photo: {e}")
        return "Failed to save photo!", 500

    # 이미지를 TensorRT 모델 입력 형식으로 전처리
    try:
        img = cv2.imread(filepath)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  # 이미지를 흑백으로 변환
        img = cv2.resize(img, (48, 48))  # 모델 입력 크기로 조정
        img = img / 255.0  # 0~1로 정규화
        img = np.expand_dims(img, axis=(0, 1))  # 배치 및 채널 차원 추가

        # TensorRT 모델로 감정 예측
        predictions = infer_with_tensorrt(img)
        emotion_index = np.argmax(predictions)  # 가장 높은 확률의 감정 인덱스
        original_emotion = emotion_labels[emotion_index]  # 원래 영어 레이블 가져오기
        emotion = custom_labels[original_emotion]  # 사용자 정의 레이블로 매핑
    except Exception as e:
        print(f"Emotion prediction failed: {e}")
        emotion = "알 수 없음"  # 예측 실패 시 기본값 설정

    session['last_emotion'] = emotion  # 세션에 예측된 감정 저장
    print(f"Predicted emotion: {emotion}")

    return render_template('save.html', filename=filename, emotion=emotion)

# 오늘의 일기 작성
@app.route('/today', methods=['GET', 'POST'])
def today():
    """
    오늘의 일기를 작성하고 저장하거나, 작성 화면을 반환하는 함수
    """
    if request.method == 'POST':
        diary_text = request.form.get('diary')  # 작성된 일기 가져오기
        emoji = request.form.get('emoji', session.get('last_emotion', 'default.png'))  # 감정 가져오기
        date = datetime.now().strftime('%Y-%m-%d')  # 현재 날짜 가져오기

        # 일기 파일에 저장
        with open(DIARY_FILE, 'a') as f:
            f.write(f"{date} - {emoji}: {diary_text}\n")

        return redirect(url_for('list_diary'))  # 일기 목록 페이지로 리다이렉트

    emoji = session.get('last_emotion', 'default.png')  # 마지막 예측된 감정 가져오기
    return render_template('today.html', emoji=emoji)

# 일기 목록
@app.route('/list')
def list_diary():
    """
    저장된 일기 목록을 반환하는 함수
    """
    diaries = []
    if os.path.exists(DIARY_FILE):  # 일기 파일이 존재하는 경우
        with open(DIARY_FILE, 'r') as f:
            diaries = f.readlines()  # 파일에서 모든 일기 읽기

        # 일기가 10개를 초과하면 오래된 일기를 삭제
        if len(diaries) > 10:
            diaries = diaries[-10:]  # 최근 10개만 유지
            with open(DIARY_FILE, 'w') as f:
                f.writelines(diaries)  # 수정된 목록 저장

    return render_template('list.html', diaries=diaries)

# 게임 화면
@app.route('/game')
def game():
    """
    게임 화면을 반환하는 함수
    """
    return render_template('game.html')

# 애플리케이션 실행
if __name__ == '__main__':
    app.run(debug=True)  # 디버그 모드로 Flask 애플리케이션 실행
