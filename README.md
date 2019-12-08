# text-detection-ctpn
基于 CTPN 的文本检测。在 [text-detection-ctpn/](https://github.com/eragonruan/text-detection-ctpn/)  项目基础上做了些优化工作。

# 编译配置

## 环境配置
```sh
# 创建环境
conda create --name python3 python=3.7
# 切换到新创建的环境
conda activate python3
# 升级 pip 版本
python -m pip install -i https://mirrors.huaweicloud.com/repository/pypi/simple pip --upgrade
# 使用华为的 pip 源
pip config set global.index-url https://mirrors.huaweicloud.com/repository/pypi/simple
```

## 安装依赖

### 安装 
Anaconda 下载页：`https://www.anaconda.com/distribution/`

### 安装 Visual Studio
Visual Studio 下载页： `https://visualstudio.microsoft.com/zh-hans/vs/`。下载开源版本即可。本项目中使用的版本：`Visual Studio Community 2019`.

### 安装 CUDA 和 cuDNN
CUDA 和 cuDNN 版本需要对应。
+ CUDA 下载地址：`https://developer.nvidia.com/cuda-toolkit-archive`
+ cuDNN 下载地址：`https://developer.nvidia.com/rdp/cudnn-archive`


### 安装 python 依赖
```sh
pip install opencv-python
pip install tensorflow-gpu==1.13.1
pip install numpy

# 用于编译 bbox 和 nms 模块
pip install Cython

#### 以下是可选模块 ####

# web 需要依赖此模块
pip install flask

# web 服务中异步回调依赖此模块
pip install requests
```

## 编译 bbox 和 nms 工具
Linux：
```shell
cd utils/bbox
chmod +x make.sh
./make.sh
```
windows：
```bat
cd utils/bbox
make.bat
```

# 使用

## 配置模型
下载 ckpt 文件。 下载链接：[百度云盘](https://pan.baidu.com/s/1BNHt_9fiqRPGmEXPaxaFXw)。下载完成后，解压。将解压后的 `checkpoints_mlt/` 放到源码根目录下。

## 运行demo

### 普通 demo
在源码根目录下执行：`python demo/demo.py`
### web demo
在源码根目录下执行：
```sh
python main\web.py --host=0.0.0.0 --port=20000 --homeDir=.\tmp\ --ctpnDebug=True
```

## 开发
```py
# 引入 CTPN 类
from main.ctpn import CTPN

# 创建实例
ctpn = CTPN()

# 添加任务
ctpn.addWorker('demo/img/001.jpg')

# 开始处理
ctpn.start()
```

# 参考
+ https://github.com/eragonruan/text-detection-ctpn/
+ https://arxiv.org/abs/1609.03605
