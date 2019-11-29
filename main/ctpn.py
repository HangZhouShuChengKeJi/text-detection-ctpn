# coding=utf-8
import logging

import os
import shutil
import sys
import time
import queue
import json

import cv2
import numpy as np
import tensorflow as tf

# sys.path.append(os.getcwd())
from nets import model_train as model
from utils.rpn_msr.proposal_layer import proposal_layer
from utils.text_connector.detectors import TextDetector

logger = logging.getLogger(__file__)

class CTPN:
    # 停止信号
    SIGNAL_STOP = '__stop__'

    def __init__(self, debug = False):
        self.workerQueue = queue.Queue(1000)
        self.outputPath = 'demo/output/'
        self.checkpoint_path = 'checkpoints_mlt/'
        self.running = False
        self.debug = debug
        return

    def addWorker(self, imgFilePath) :
        if self.workerQueue:
            logger.debug("接收到文件： %s", imgFilePath)
            self.workerQueue.put_nowait(imgFilePath)
            return True
        return False

    def stop(self) :
        self.running = False
        self.addWorker(SIGNAL_STOP)

    def is_stop_signal(self, signal) -> bool:
        return signal == CTPN.SIGNAL_STOP
    
    def close(self) :
        self.workerQueue = None

    def wrapResult(self, boxes: list, scores: list) -> dict :
        result = {
            'words_result': [], 
            'words_result_num': -1
            }
        for i, box in enumerate(boxes) :
            result['words_result'].append({
                'words': None, 
                'score': str(scores[i]), 
                'location': {
                    'top': int(box[1]),
                    'left': int(box[0]),
                    'width': int(box[2] - box[0]),
                    'height': int(box[5] - box[1])
                }
            })

        return result

    def resize_image(self, img):
        # 图片形状（高宽）
        img_size = img.shape
        im_size_min = np.min(img_size[0:2])
        im_size_max = np.max(img_size[0:2])

        # 保证图片尺寸小于等于 600 * 1200
        im_scale = float(600) / float(im_size_min)
        if np.round(im_scale * im_size_max) > 1200:
            im_scale = float(1200) / float(im_size_max)
        new_h = int(img_size[0] * im_scale)
        new_w = int(img_size[1] * im_scale)

        new_h = new_h if new_h // 16 == 0 else (new_h // 16 + 1) * 16
        new_w = new_w if new_w // 16 == 0 else (new_w // 16 + 1) * 16

        # 缩放图片
        re_im = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        return re_im, (new_h / img_size[0], new_w / img_size[1])
    
    def start(self) :
        self.running = True

        tf.app.flags.DEFINE_string('gpu', '0', '')
        # 已经训练好的模型加载路径
        tf.app.flags.DEFINE_string('checkpoint_path', self.checkpoint_path, '')

        # 图
        with tf.compat.v1.get_default_graph().as_default():
            # 占位符 - 输入图片
            input_image = tf.compat.v1.placeholder(tf.float32, shape=[None, None, None, 3], name='input_image')
            # 占位符 - 输入图片信息
            input_im_info = tf.compat.v1.placeholder(tf.float32, shape=[None, 3], name='input_im_info')

            # 创建一个变量 global_step
            global_step = tf.compat.v1.get_variable('global_step', [], initializer=tf.constant_initializer(0), trainable=False)

            # tensorflow op
            bbox_pred, cls_pred, cls_prob = model.model(input_image)

            variable_averages = tf.train.ExponentialMovingAverage(0.997, global_step)
            saver = tf.compat.v1.train.Saver(variable_averages.variables_to_restore())

            # tensorflow session 配置
            sessionConfig = tf.compat.v1.ConfigProto(allow_soft_placement=True) 
            # 显存占用率
            # sessionConfig.gpu_options.per_process_gpu_memory_fraction = 0.3
            # 动态申请内存
            sessionConfig.gpu_options.allow_growth = True

            with tf.compat.v1.Session(config=sessionConfig) as sess:

                # 基于 checkpoint 文件(ckpt)加载参数
                ckpt_state = tf.compat.v1.train.get_checkpoint_state(self.checkpoint_path)

                # 模型路径
                model_path = os.path.join(self.checkpoint_path, os.path.basename(ckpt_state.model_checkpoint_path))

                logger.info(u'Restore from {}'.format(model_path))

                # 恢复变量
                saver.restore(sess, model_path)

                while self.running:

                    logger.info(u'等待接收图片')

                    imgFilePath = self.workerQueue.get()
                    if self.is_stop_signal(imgFilePath):
                        logger.info(u'接收到队列停止信号')
                        break

                    logger.info(u'开始处理图片： {}'.format(imgFilePath))

                    # 开始计时
                    start = time.time()
                    try:
                        im = cv2.imread(imgFilePath)[:, :, ::-1]
                    except:
                        logger.exception(sys.exc_info())
                        continue

                    # 压缩图片尺寸，不超过 600 * 1200
                    img, (rh, rw) = self.resize_image(im)
                    # 高、宽、通道数
                    h, w, c = img.shape
                    im_info = np.array([h, w, c]).reshape([1, 3])

                    # 执行运算
                    bbox_pred_val, cls_prob_val = sess.run([bbox_pred, cls_prob],
                                                        feed_dict={input_image: [img],
                                                                    input_im_info: im_info})

                    # 根据RPN目标回归值修正anchors并做排序、nms等后处理输出由proposal坐标和batch_ind全0索引组成的blob
                    textsegs, _ = proposal_layer(cls_prob_val, bbox_pred_val, im_info)
                    scores = textsegs[:, 0]
                    textsegs = textsegs[:, 1:5]

                    textdetector = TextDetector(DETECT_MODE='H')
                    boxes = textdetector.detect(textsegs, scores[:, np.newaxis], img.shape[:2])

                    # 结束计时

                    logger.info(u'总计耗时： {}'.format(time.time() - start))

                    if self.debug:
                        with open(os.path.join(self.outputPath, os.path.splitext(os.path.basename(imgFilePath))[0]) + ".json",
                                "w") as f:
                            f.writelines(json.dumps(self.wrapResult(boxes, scores)))

                        # 将 python 数组 转换为 numpy 数组
                        boxes = np.array(boxes, dtype=np.int)

                        for i, box in enumerate(boxes):
                            cv2.polylines(img, [box[:8].astype(np.int32).reshape((-1, 1, 2))], True, color=(0, 255, 0),
                                        thickness=2)
                        img = cv2.resize(img, None, None, fx=1.0 / rh, fy=1.0 / rw, interpolation=cv2.INTER_LINEAR)

                        cv2.imwrite(os.path.join(self.outputPath, os.path.basename(imgFilePath)), img[:, :, ::-1])

                        with open(os.path.join(self.outputPath, os.path.splitext(os.path.basename(imgFilePath))[0]) + ".txt",
                                "w") as f:
                            for i, box in enumerate(boxes):
                                line = ",".join(str(box[k]) for k in range(8))
                                line += "," + str(scores[i]) + "\n"
                                f.writelines(line)
        
if __name__ == '__main__':

    ctpn = CTPN()
    ctpn.addWorker('demo/img/001.jpg')
    ctpn.start()

