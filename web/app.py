<!DOCTYPE html>
<html>
<head>
    <title>Start Page</title>
    <!-- 외부 스타일 시트 연결 -->
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    <style>
        /* 전체 body 스타일 설정 */
        body {
            font-family: Arial, sans-serif; /* 폰트 설정 */
            margin: 0; /* 여백 제거 */
            padding: 0; /* 패딩 제거 */
            background-color: #f8f8f8; /* 배경색 설정 */
            height: 100vh; /* 전체 화면 높이 설정 */
            display: flex; /* 플렉스박스로 중앙 정렬 */
            justify-content: center; /* 수평 중앙 정렬 */
            align-items: center; /* 수직 중앙 정렬 */
        }

        /* 시작 화면 컨테이너 스타일 */
        .start-container {
            position: relative; /* 위치 설정을 위해 relative 사용 */
            width: 100%; /* 화면 너비 전체 사용 */
            height: 100%; /* 화면 높이 전체 사용 */
            background-image: url('{{ url_for('static', filename='images/start_background.png') }}'); /* 배경 이미지 설정 */
            background-size: cover; /* 배경 이미지 크기 조정 */
            background-position: center; /* 배경 이미지 중앙 정렬 */
        }

        /* 제목 스타일 */
        h1 {
            position: absolute; /* 위치 절대 설정 */
            top: 30px; /* 상단에서 30px 아래 위치 */
            left: 50%; /* 화면의 수평 중앙 */
            transform: translateX(-50%); /* 수평 중앙 정렬 */
            font-size: 39px; /* 텍스트 크기 증가 */
            margin: 0; /* 여백 제거 */
            text-align: center; /* 텍스트 중앙 정렬 */
            line-height: 1.2; /* 줄 간격 조정 */
        }

        /* 설명 문구 스타일 */
        p {
            position: absolute; /* 위치 절대 설정 */
            top: 150px; /* 상단에서 150px 아래 위치 */
            left: 50%; /* 화면의 수평 중앙 */
            transform: translateX(-50%); /* 수평 중앙 정렬 */
            font-size: 20px; /* 텍스트 크기 설정 */
            color: #666; /* 텍스트 색상 설정 */
            text-align: center; /* 텍스트 중앙 정렬 */
            line-height: 1.6; /* 줄 간격 조정 */
        }

        /* 시작 버튼 스타일 */
        .start-button {
            position: absolute; /* 위치 절대 설정 */
            top: 50%; /* 화면의 수직 중앙 */
            left: 50%; /* 화면의 수평 중앙 */
            transform: translate(-50%, -50%); /* 중앙 정렬 */
            padding: 15px 30px; /* 버튼 패딩 */
            font-size: 20px; /* 버튼 텍스트 크기 */
            background-color: #87CEFA; /* 버튼 배경색 */
            border: none; /* 버튼 테두리 제거 */
            border-radius: 5px; /* 버튼 둥근 모서리 */
            color: white; /* 버튼 텍스트 색상 */
            cursor: pointer; /* 커서 모양 설정 */
            text-decoration: none; /* 링크 밑줄 제거 */
        }

        /* 시작 버튼 호버 효과 */
        .start-button:hover {
            background-color: #4682B4; /* 버튼 호버 시 배경색 변경 */
        }
    </style>
</head>
<body>
    <!-- 시작 화면 컨테이너 -->
    <div class="start-container">
        <!-- 제목 -->
        <h1>당신의 하루는<br>어땠나요?</h1>
        <!-- 설명 문구 -->
        <p>오늘도, 내일도 당신처럼<br>빛나는 하루가 계속 되길.</p>
        <!-- 시작 버튼 -->
        <a href="{{ url_for('index') }}" class="start-button">START</a>
    </div>
</body>
</html>
