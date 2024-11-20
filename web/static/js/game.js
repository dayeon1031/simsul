// 표정 배열 초기화
let expressions = ["기쁨", "당황", "분노", "슬픔"]; // 게임에서 사용할 표정 목록
let score = 0; // 점수 초기화
let video = document.getElementById('video'); // HTML 비디오 요소 가져오기

// 카메라 스트림 시작
navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => {
        video.srcObject = stream; // 비디오 요소에 스트림 연결
        console.log("Camera stream started."); // 카메라 스트림 성공 메시지
    })
    .catch(err => console.error("Camera error:", err)); // 카메라 스트림 실패 메시지

// 게임 시작 함수
function startGame() {
    // 랜덤으로 표정을 선택하여 사용자에게 요청
    let randomExpression = expressions[Math.floor(Math.random() * expressions.length)];
    document.getElementById('expression').innerText = `Make this expression: ${randomExpression}`;

    let countdown = 3; // 카운트다운 시작 시간
    document.getElementById('result').innerText = ''; // 결과 메시지 초기화

    // 카운트다운 타이머 설정
    const timer = setInterval(() => {
        document.getElementById('countdown').innerText = `Time left: ${countdown} seconds`; // 남은 시간 표시
        countdown--;

        if (countdown < 0) {
            clearInterval(timer); // 타이머 정지
            takePhoto(); // 사진 캡처
            evaluateExpression(randomExpression); // 표정 평가
        }
    }, 1000); // 1초 간격으로 타이머 실행
}

// 사진 캡처 함수
function takePhoto() {
    const canvas = document.createElement('canvas'); // 캔버스 요소 생성
    const context = canvas.getContext('2d'); // 캔버스 2D 컨텍스트 가져오기
    canvas.width = video.videoWidth; // 캔버스 너비 설정
    canvas.height = video.videoHeight; // 캔버스 높이 설정
    context.drawImage(video, 0, 0, canvas.width, canvas.height); // 비디오 이미지를 캔버스에 그리기

    console.log("Photo captured! (Simulated)"); // 캡처된 이미지 로직 (서버 전송 추가 가능)
}

// 표정 평가 함수
function evaluateExpression(expectedExpression) {
    // 실제로는 사용자 표정을 분석하는 AI 모델 호출 로직 추가 가능
    const userExpression = "기쁨"; // 현재는 하드코딩된 값, 실제로는 AI 모델의 결과를 사용
    let resultMessage = ''; // 결과 메시지 변수

    // 사용자 표정이 예상 표정과 일치하는지 확인
    if (userExpression === expectedExpression) {
        score++; // 점수 증가
        resultMessage = `Correct! Score: ${score}`; // 정답 메시지
        document.getElementById('result').style.color = 'green'; // 결과 텍스트 색상 설정
    } else {
        resultMessage = `Wrong! Expected: ${expectedExpression}, but got: ${userExpression}`; // 오답 메시지
        document.getElementById('result').style.color = 'red'; // 결과 텍스트 색상 설정
    }

    // 결과 및 점수 업데이트
    document.getElementById('result').innerText = resultMessage; // 결과 메시지 출력
    document.getElementById('score').innerText = `Score: ${score}`; // 점수 출력
}
