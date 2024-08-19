from flask import Flask, request, render_template, send_from_directory
from concurrent.futures import ThreadPoolExecutor
import imgProcess
import os

app = Flask(__name__, template_folder='front')
executor = ThreadPoolExecutor(max_workers=2)

@app.route('/')
def index():
    return render_template('uploadImg.html')

@app.route('/upload', methods=['POST'])
def upload():
    latitude = request.form['latitude']
    longitude = request.form['longitude']
    imgFilePath = request.form['imgFilePath']
    
    # prc() 함수를 비동기적으로 실행
    executor.submit(imgProcess.prc, imgFilePath)
    
    # 처리 중 메시지와 함께 landing.html 렌더링
    return render_template('landing.html', message='처리 중')

@app.route('/check_status', methods=['GET'])
def check_status():
    # 여기서 prc() 함수의 완료 여부를 확인하는 로직을 구현해야 합니다.
    # 이 예제에서는 간단히 항상 완료되었다고 가정합니다.
    is_completed = True
    
    if is_completed:
        return '처리 완료'
    else:
        return '처리 중'

@app.route('/front/<path:filename>')
def serve_static(filename):
    return send_from_directory('front', filename)

if __name__ == '__main__':
    app.run(debug=True)