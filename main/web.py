# coding=utf-8
import sys
import os
import threading

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(name)s - %(message)s')

from flask import Flask
from flask import request
from flask import appcontext_tearing_down

sys.path.append(os.getcwd())

from main.ctpn import CTPN

app = Flask(__name__)

# 文件上传路径
app.config['UPLOAD_FOLDER'] = 'C:\\Users\\hanyufei\\Workspace\\python\\'
# 文件上传尺寸限制
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# 支持上传的文件名后缀
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

# ctpn 服务
ctpnService = CTPN(debug = True)

def ctpnServiceRun():
    app.logger.info("启动 CTPN 服务")
    ctpnService.start()
    app.logger.warn("CTPN 服务退出")

# 释放资源
def releaseResourceOnDown(sender, **extra):
    ctpnService.stop()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/api/ocr.htm', methods=['GET', 'POST'])
def api_ocr():
    if request.method == 'GET':
        return 'Hello, World!'
    elif request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            return 'No file!'
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            return 'No file!'
        if file and allowed_file(file.filename):
            # filename = secure_filename(file.filename)
            imgFilePath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(imgFilePath)
            ctpnService.addWorker(imgFilePath)
            return 'upload success'
        return 'File type error!'
    return 'unknown method!'


if __name__ == '__main__':
    # ctpn 线程
    ctpnThread = threading.Thread(target=ctpnServiceRun, name='ctpn')

    app.logger.info("启动 CTPN 服务线程...")
    ctpnThread.start()
    app.logger.info("启动 CTPN 服务线程成功")

    app.logger.info("启动 web 服务...")
    app.run(host='0.0.0.0', port=20000)
    app.logger.info("web 服务停止")

    app.logger.info("终止 CTPN 服务...")
    ctpnService.stop()
    app.logger.info("等待 CTPN 服务线程退出...")
    ctpnThread.join()
    app.logger.info("终止 CTPN 服务成功")
