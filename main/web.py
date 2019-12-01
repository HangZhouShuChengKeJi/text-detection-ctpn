# coding=utf-8
import sys
import os
import threading
import getopt
import queue
import json

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(name)s - %(message)s')

# http 请求模块
import requests

from flask import Flask
from flask import request

sys.path.append(os.getcwd())

from main.ctpn import CTPN

logger = logging.getLogger(__file__)

app = Flask(__name__)

# ctpn 工作队列。通过该队列将文件传递给 ctpn 服务
ctpnWorkerQueue = queue.Queue(1000)

# 等待回调的图片字典，图片文件路径作为字典的 key
waitCallbackDict = {'fileName': 'url'}

# 支持上传的文件名后缀
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ctpnCallback(fileName, ctpnRes) :
    # todo 回调改为异步
    if fileName in waitCallbackDict :
        url = waitCallbackDict.get(fileName)
        try:
            response = requests.post(url = url, data=json.dumps(ctpnRes), headers={'Content-type': 'application/json'})
            if response.status_code == 200 :
                logger.info('回调成功')
                waitCallbackDict.pop(fileName)
                return
            logger.warning('回调失败')
        except Exception as e:
            logger.exception('回调异常', e)

@app.route('/', methods=['GET'])
def hello_world():
    return 'Hello, CTPN !'

@app.route('/api/ctpn.htm', methods=['GET', 'POST'])
def api_ocr():
    """
        请求参数：
            ctpnImg: 需要识别的图片文件
            callbackUrl: 回调地址。识别结束后，异步通知处理结果
    """
    if request.method == 'GET':
        return 'Hello, CTPN !'
    elif request.method == 'POST':
        if 'ctpnImg' not in request.files:
            return 'No image!'
        file = request.files['ctpnImg']
        if file.filename == '':
            return 'No image!'
        if file and allowed_file(file.filename):
            # 保存文件到本地
            imgFilePath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(imgFilePath)

            # 添加到待回调集合
            waitCallbackDict[imgFilePath] = request.form['callbackUrl']
            # 提交到 ctpn 工作队列
            ctpnWorkerQueue.put(imgFilePath)
            return 'ok'
        return 'Image type error!'
    return 'unknown method!'

def main(host, port, workDir, ctpnDebug):

    # 转换上传路径为绝对路径
    uploadDir = os.path.abspath(os.path.join(workDir, 'upload'))
    if not os.path.exists(uploadDir) :
        os.makedirs(name = uploadDir, exist_ok = True)
        logger.info('创建上传路径：{}'.format(uploadDir))

    # 转换上传路径为绝对路径
    outputDir = os.path.abspath(os.path.join(workDir, 'output'))
    if not os.path.exists(outputDir) :
        os.makedirs(name = outputDir, exist_ok = True)
        logger.info('创建输出路径：{}'.format(outputDir))


    # 文件上传路径
    app.config['UPLOAD_FOLDER'] = uploadDir
    # 文件上传尺寸限制
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    
    # ctpn 服务
    ctpnService = CTPN(workerQueue = ctpnWorkerQueue, callback = ctpnCallback, outputPath = outputDir, debug = ctpnDebug)

    def ctpnServiceRun():
        logger.info("启动 CTPN 服务")
        ctpnService.start()
        logger.warn("CTPN 服务退出")

    # ctpn 线程
    ctpnThread = threading.Thread(target=ctpnServiceRun, name='ctpn')

    logger.info("启动 CTPN 服务线程...")
    ctpnThread.start()
    logger.info("启动 CTPN 服务线程成功")

    logger.info("启动 web 服务...")

    app.run(host=host, port=port)

    logger.info("web 服务停止")

    logger.info("终止 CTPN 服务...")
    ctpnService.stop()
    logger.info("等待 CTPN 服务线程退出...")
    ctpnThread.join()
    logger.info("终止 CTPN 服务成功")


def usage():
    print("Usage:")
    print("    --host\t\t flask 绑定的 IP 地址，默认：0.0.0.0")
    print("    --port\t\t flask 绑定的端口，默认：20000")
    print("    --workDir\t\t 工作路径")
    print("    --ctpnDebug\t\t ctpn 调试开关。True：生成调试图片供参考")
    print("    --help\t\t 删除帮助信息")
    print("")

if __name__ == '__main__':
    """
    python main\web.py 
    """
    options, args = getopt.getopt(sys.argv[1:], '', ["help", "host=", "port=", "workDir=", "ctpnDebug="])

    optionDict = {}
    for option in options:
        optionDict[option[0]] = None if len(option) == 1 else option[1]

    if '--help' in optionDict :
        usage()
        sys.exit()
    else :
        main(host=optionDict.get('--host', '0.0.0.0')
        , port=int(optionDict.get('--port', '20000'))
        , workDir=optionDict.get('--workDir')
        , ctpnDebug=bool(optionDict.get('--ctpnDebug', False)))


