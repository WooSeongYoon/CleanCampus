from flask import Flask, request, render_template, send_from_directory
from concurrent.futures import ThreadPoolExecutor, Future
import imgProcess
import os

app = Flask(__name__, template_folder='front')
executor = ThreadPoolExecutor(max_workers=2)

# prc 실행의 Future를 저장할 전역 변수
prc_future = None

@app.route('/')
def index():
    return render_template('uploadImg.html')

@app.route('/upload', methods=['POST'])
def upload():
    global prc_future
    latitude = request.form['latitude']
    longitude = request.form['longitude']
    img = request.files['image']  # 이 부분을 수정했습니다

    print(latitude, longitude)
    # prc() 함수를 비동기적으로 실행하고 Future 객체 저장
    prc_future = executor.submit(imgProcess.prc, img)
    
    # 처리 중 메시지와 함께 landing.html 렌더링
    return render_template('landing.html', message='처리 중')

@app.route('/check_status', methods=['GET'])
def check_status():
    global prc_future
    if prc_future is None:
        return '처리 중'
    elif prc_future.done():
        return '처리 완료'
    else:
        return '처리 중'

@app.route('/front/<path:filename>')
def serve_static(filename):
    return send_from_directory('front', filename)

if __name__ == '__main__':
    app.run(debug=True)