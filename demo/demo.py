
import sys
import os

sys.path.append(os.getcwd())

from main.ctpn import CTPN

if __name__ == '__main__':

    ctpn = CTPN()
    ctpn.addWorker('demo/img/001.jpg')
    ctpn.start()