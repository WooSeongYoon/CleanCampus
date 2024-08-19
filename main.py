from flask import Flask, request, render_template, send_from_directory, redirect, url_for, jsonify, abort
from concurrent.futures import ThreadPoolExecutor, Future, TimeoutError
import imgProcess
import os
import time
import json

app = Flask(__name__, template_folder='front')
executor = ThreadPoolExecutor(max_workers=2)

class LocPoint:
    def __init__(self, latitude, longitude, name, summary, isPreSet=True, image_path=None):
        self.latitude = latitude
        self.longitude = longitude
        self.name = name
        self.summary = summary  # 새로 추가된 필드
        self.isPreSet = isPreSet
        self.image_path = image_path
        self.workDone = False
        self.result = None

loc_points = []
prc_future = None
prc_start_time = None
current_point_index = None

@app.route('/')
def index():
    return render_template('uploadImg.html')

@app.route('/upload', methods=['POST'])
def upload():
    global prc_future, prc_start_time, current_point_index
    
    try:
        latitude = request.form['latitude']
        longitude = request.form['longitude']
        summary = request.form['summary']  # 새로 추가된 필드
        img = request.files['image']

        if not latitude or not longitude:
            return "위치 정보가 없습니다. 위치 정보를 허용해주세요.", 400

        if not summary:
            return "쓰레기 요약 정보를 입력해주세요.", 400

        if not img:
            return "이미지를 업로드해주세요.", 400

        img_path = os.path.join('temp', img.filename)
        img.save(img_path)

        new_point = LocPoint(latitude, longitude, "Unknown", summary, False, img_path)
        loc_points.append(new_point)
        current_point_index = len(loc_points) - 1

        prc_future = executor.submit(imgProcess.prc, img_path)
        prc_start_time = time.time()
        
        return redirect(url_for('landing'))
    except Exception as e:
        return f"오류가 발생했습니다: {str(e)}", 500

# '/workflow' 경로에 대한 GET 요청 처리
@app.route('/workflow')
def workflow():
    # workflow.html 템플릿을 렌더링하여 반환합니다.
    return render_template('workflow.html')

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
        result = prc_future.result(timeout=0.1)

        if current_point_index is not None:
            loc_points[current_point_index].workDone = True
            loc_points[current_point_index].result = result

        if isinstance(result, str) and result.startswith('Fail,'):
            number_after_comma = result.split(',')[1]
            return f'쓰레기가 감지되지 않음: {number_after_comma}'
        
        elif isinstance(result, str) and result.startswith('Success,'):
            number_after_comma = result.split(',')[1]
            return f'쓰레기가 감지됨: {number_after_comma}'

        return '처리 완료'
    except TimeoutError:
        if elapsed_time < 60:
            return '처리 중'
        else:
            return '처리 지연'
    except Exception as e:
        if current_point_index is not None:
            loc_points[current_point_index].workDone = True
            loc_points[current_point_index].result = str(e)
        return f'오류 발생: {str(e)}'

@app.route('/front/<path:filename>')
def serve_static(filename):
    return send_from_directory('front', filename)

@app.route('/d', methods=['GET'])
def get_loc_points():
    loc_points_dict = [vars(point) for point in loc_points]
    return jsonify(loc_points_dict)

@app.route('/update/<int:id>', methods=['GET'])
def update_loc_point(id):
    if id < 0 or id >= len(loc_points):
        abort(404)
    
    loc_point = loc_points[id]
    return render_template('updateLoc.html', point=loc_point, id=id)

if __name__ == '__main__':
    if not os.path.exists('temp'):
        os.makedirs('temp')
    app.run(debug=True)