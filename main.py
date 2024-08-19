# 필요한 모듈들을 임포트합니다.
from flask import Flask, request, render_template, send_from_directory, redirect, url_for, jsonify
from concurrent.futures import ThreadPoolExecutor, Future, TimeoutError
import imgProcess
import os
import time
import json

# Flask 애플리케이션을 생성하고 템플릿 폴더를 'front'로 설정합니다.
app = Flask(__name__, template_folder='front')
# 최대 2개의 작업을 동시에 실행할 수 있는 ThreadPoolExecutor를 생성합니다.
executor = ThreadPoolExecutor(max_workers=2)

# LocPoint 클래스 정의
class LocPoint:
    # 클래스 초기화 메서드
    def __init__(self, latitude, longitude, name, isPreSet=True, image_path=None):
        self.latitude = latitude  # 위도 정보
        self.longitude = longitude  # 경도 정보
        self.name = name  # 건물 또는 위치 이름
        self.isPreSet = isPreSet  # 기본 값은 True로, 기본적으로 설정된 지점을 나타냄
        self.image_path = image_path  # 처리할 이미지의 경로
        self.workDone = False  # 작업 완료 여부를 나타내는 bool 속성
        self.result = None  # 처리 결과를 저장할 속성 추가

# 전역 변수로 클래스 배열 생성
loc_points = []

# prc 실행의 Future를 저장할 전역 변수
prc_future = None
# prc 시작 시간을 저장할 전역 변수
prc_start_time = None
# 현재 처리 중인 LocPoint의 인덱스
current_point_index = None

# 루트 경로에 대한 라우트 설정
@app.route('/')
def index():
    # uploadImg.html 템플릿을 렌더링하여 반환합니다.
    return render_template('uploadImg.html')

# '/upload' 경로에 대한 POST 요청 처리
@app.route('/upload', methods=['POST'])
def upload():
    # 전역 변수를 사용하기 위해 global 키워드 사용
    global prc_future, prc_start_time, current_point_index
    # 폼에서 위도와 경도 정보를 가져옵니다.
    latitude = request.form['latitude']
    longitude = request.form['longitude']
    # 업로드된 이미지 파일을 가져옵니다.
    img = request.files['image']

    # 이미지를 임시로 저장합니다.
    img_path = os.path.join('temp', img.filename)
    img.save(img_path)

    # 새로운 LocPoint 객체를 생성하고 배열에 추가합니다.
    new_point = LocPoint(latitude, longitude, "Unknown", False, img_path)
    loc_points.append(new_point)
    # 현재 처리 중인 포인트의 인덱스를 설정합니다.
    current_point_index = len(loc_points) - 1

    # prc() 함수를 비동기적으로 실행하고 Future 객체를 저장합니다.
    prc_future = executor.submit(imgProcess.prc, img_path)
    # 처리 시작 시간을 기록합니다.
    prc_start_time = time.time()
    
    # landing.html로 리다이렉트합니다.
    return redirect(url_for('landing'))

# '/landing' 경로에 대한 라우트 설정
@app.route('/landing')
def landing():
    # landing.html 템플릿을 렌더링하여 반환합니다.
    return render_template('landing.html', message='처리 중')

# '/check_status' 경로에 대한 GET 요청 처리
@app.route('/check_status', methods=['GET'])
def check_status():
    # 전역 변수를 사용하기 위해 global 키워드 사용
    global prc_future, prc_start_time, current_point_index
    # prc_future가 None이면 '처리 중'을 반환합니다.
    if prc_future is None:
        return '처리 중'

    # 경과 시간을 계산합니다.
    elapsed_time = time.time() - prc_start_time

    try:
        # 0.1초 동안 결과를 기다립니다.
        result = prc_future.result(timeout=0.1)

        if current_point_index is not None:
            # 작업 완료 상태를 True로 설정합니다.
            loc_points[current_point_index].workDone = True
            loc_points[current_point_index].result = result

        # 'Fail,<number>' 형식에 대한 검사
        if isinstance(result, str) and result.startswith('Fail,'):
            number_after_comma = result.split(',')[1]
            return f'쓰레기가 감지되지 않음: {number_after_comma}'
        
        # 'Success,<number>' 형식에 대한 검사
        elif isinstance(result, str) and result.startswith('Success,'):
            number_after_comma = result.split(',')[1]
            return f'쓰레기가 감지됨: {number_after_comma}'

        return '처리 완료'
    except TimeoutError:
        # 아직 처리 중인 경우
        if elapsed_time < 60:  # prc() 함수가 60초 정도 소요된다고 가정
            return '처리 중'
        else:
            return '처리 지연'
    except Exception as e:
        # 오류 발생 시
        if current_point_index is not None:
            # 작업 완료 상태를 True로 설정합니다.
            loc_points[current_point_index].workDone = True
            loc_points[current_point_index].result = str(e)
        return f'오류 발생: {str(e)}'

# 정적 파일 서빙을 위한 라우트 설정
@app.route('/front/<path:filename>')
def serve_static(filename):
    # front 디렉토리에서 정적 파일을 서빙합니다.
    return send_from_directory('front', filename)

# '/d' 경로에 대한 GET 요청 처리
@app.route('/d', methods=['GET'])
def get_loc_points():
    # LocPoint 객체를 딕셔너리로 변환
    loc_points_dict = [vars(point) for point in loc_points]
    # JSON으로 변환하여 반환 (들여쓰기 적용)
    return jsonify(loc_points_dict)

# 메인 실행 부분
if __name__ == '__main__':
    # 'temp' 디렉토리가 없으면 생성합니다.
    if not os.path.exists('temp'):
        os.makedirs('temp')
    # Flask 애플리케이션을 디버그 모드로 실행합니다.
    app.run(debug=True)