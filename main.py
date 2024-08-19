from flask import Flask, request, render_template, send_from_directory, redirect, url_for
from concurrent.futures import ThreadPoolExecutor, Future, TimeoutError
import imgProcess
import os
import time

app = Flask(__name__, template_folder='front')
executor = ThreadPoolExecutor(max_workers=2)

# 상수 형태의 타입 정의
class PointTypes:
    USER_REPORT = '사용자제보'
    ADMIN_ADDITION = '관리자추가'

# LocPoint 클래스 정의
class LocPoint:
    def __init__(self, latitude, longitude, building_name, point_type, image_path):
        self.latitude = latitude
        self.longitude = longitude
        self.building_name = building_name
        self.point_type = point_type
        self.image_path = image_path
        self.workDone = False  # 작업 완료 여부를 나타내는 bool 속성 추가

# 전역 변수로 클래스 배열 생성
loc_points = []

# prc 실행의 Future를 저장할 전역 변수
prc_future = None
prc_start_time = None
current_point_index = None  # 현재 처리 중인 LocPoint의 인덱스

@app.route('/')
def index():
    return render_template('uploadImg.html')

@app.route('/upload', methods=['POST'])
def upload():
    global prc_future, prc_start_time, current_point_index
    latitude = request.form['latitude']
    longitude = request.form['longitude']
    img = request.files['image']

    # 이미지를 임시로 저장
    img_path = os.path.join('temp', img.filename)
    img.save(img_path)

    # 새로운 LocPoint 생성 및 배열에 추가
    new_point = LocPoint(latitude, longitude, "Unknown", PointTypes.USER_REPORT, img_path)
    loc_points.append(new_point)
    current_point_index = len(loc_points) - 1

    # prc() 함수를 비동기적으로 실행하고 Future 객체 저장
    prc_future = executor.submit(imgProcess.prc, img_path)
    prc_start_time = time.time()

    # landing.html로 리다이렉트
    return redirect(url_for('landing'))

@app.route('/landing')
def landing():
    return render_template('landing.html', message='처리 중')

@app.route('/check_status', methods=['GET'])
def check_status():
    global prc_future, prc_start_time, current_point_index
    if prc_future is None:
        return '처리 중'

    elapsed_time = time.time() - prc_start_time

    try:
        # 0.1초 동안 결과를 기다립니다.
        result = prc_future.result(timeout=0.1)

        # 'Fail,<number>' 형식에 대한 검사
        if isinstance(result, str) and result.startswith('Fail,'):
            number_after_comma = result.split(',')[1]
            if current_point_index is not None:
                loc_points[current_point_index].workDone = True
            return f'쓰레기가 감지되지 않음: {number_after_comma}'

        if current_point_index is not None:
            loc_points[current_point_index].workDone = True
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
            loc_points[current_point_index].workDone = True
        return f'오류 발생: {str(e)}'

@app.route('/front/<path:filename>')
def serve_static(filename):
    return send_from_directory('front', filename)

if __name__ == '__main__':
    if not os.path.exists('temp'):
        os.makedirs('temp')
    app.run(debug=True)