from flask import Flask, request, render_template, send_from_directory, redirect, url_for, jsonify, abort
from concurrent.futures import ThreadPoolExecutor, Future, TimeoutError
import imgProcess
import os
import time
import json

app = Flask(__name__, template_folder='front')
app.config['JSON_AS_ASCII'] = False
executor = ThreadPoolExecutor(max_workers=2)


class LocPoint:
    def __init__(self, latitude, longitude, name, isPreSet=True, image_path=None):
        self.latitude = latitude
        self.longitude = longitude
        self.name = name
        self.isPreSet = isPreSet
        self.image_path = image_path
        self.workDone = False
        self.result = None

    def to_dict(self):
        return {
            'latitude': self.latitude,
            'longitude': self.longitude,
            'name': self.name,
            'isPreSet': self.isPreSet,
            'image_path': self.image_path,
            'workDone': self.workDone,
            'result': self.result
        }


loc_points = []

#사전 정의된 위치 주소들
loc_points.append(LocPoint(37.537797, 126.944338, "한신오피스텔", True))
loc_points.append(LocPoint(37.539235, 126.945453, "마포역", True))
loc_points.append(LocPoint(37.537796, 126.945050, "서울경찰청 금융범죄수사대", True))


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

        if not img:
            return "이미지를 업로드해주세요.", 400

        img_path = os.path.join('temp', img.filename)
        img.save(img_path)

        new_point = LocPoint(latitude, longitude, summary, False, img_path)
        loc_points.append(new_point)
        current_point_index = len(loc_points) - 1

        prc_future = executor.submit(imgProcess.prc, img_path)
        prc_start_time = time.time()

        return redirect(url_for('landing'))
    except Exception as e:
        return f"오류가 발생했습니다: {str(e)}", 500


@app.route('/update/<int:id>', methods=['POST'])
def uploadWorker(id):
    global prc_future, prc_start_time, current_point_index

    try:
        latitude = request.form['latitude']
        longitude = request.form['longitude']
        img = request.files['image']

        if not latitude or not longitude:
            return "위치 정보가 없습니다. 위치 정보를 허용해주세요.", 400

        if not img:
            return "이미지를 업로드해주세요.", 400

        img_path = os.path.join('temp', img.filename)
        img.save(img_path)

        if id < 0 or id >= len(loc_points):
            abort(404)
        current_point_index = id

        prc_future = executor.submit(imgProcess.prc, img_path)
        prc_start_time = time.time()

        return redirect(url_for('landingWorker'))
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


@app.route('/landingWorker')
def landingWorker():
    return render_template('landingWorker.html')


@app.route('/check_status', methods=['GET'])
def check_status():
    global prc_future, prc_start_time, current_point_index
    if prc_future is None:
        return '처리 중'

    elapsed_time = time.time() - prc_start_time

    try:
        result = prc_future.result(timeout=0.1)
        if current_point_index is not None:
            loc_points[current_point_index].result = result

        if isinstance(result, str) and result.startswith('Fail,'):
            loc_points[current_point_index].workDone = True
            a , b = result.split(',')[1], ""
            if not loc_points.isPreSet: # 사용자 제보만 삭제하는걸루
                loc_points.pop(current_point_index)
            return f'NotDetect,{a},{b}'

        elif isinstance(result, str) and result.startswith('Success,'):
            loc_points[current_point_index].workDone = False
            a, b = result.split(',')[1], result.split(',')[2]
            return f'Detect,{a},{b}'
    except TimeoutError:
        if elapsed_time < 60:
            return '처리 중'
        else:
            return '처리 지연'
    except Exception as e:
        if current_point_index is not None:
            loc_points[current_point_index].result = str(e)
        return f'오류 발생: {str(e)}'


@app.route('/front/<path:filename>')
def serve_front_static(filename):
    return send_from_directory('front', filename)


@app.route('/temp/<path:filename>')
def serve_temp_static(filename):
    return send_from_directory('temp', filename)


@app.route('/d', methods=['GET'])
def get_loc_points():
    loc_points_dict = [point.to_dict() for point in loc_points]
    return json.dumps(loc_points_dict, ensure_ascii=False)


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
