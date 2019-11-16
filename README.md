# text-detection-ctpn
基于 CTPN 的文本检测。

# 编译配置

## 环境配置
```sh
# 创建环境
conda create --name python3 python=3.5
# 切换到新创建的环境
conda activate python3
# 升级 pip 版本
python -m pip install -i https://mirrors.huaweicloud.com/repository/pypi/simple pip --upgrade
# 使用华为的 pip 源
pip config set global.index-url https://mirrors.huaweicloud.com/repository/pypi/simple
```

## 安装依赖
```sh
pip install opencv-python
pip install tensorflow-gpu==1.13.0
pip install Cython
pip install numpy
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

# 示例
- 下载源代码
- 下载 ckpt 文件，并解压。 [百度云盘](https://pan.baidu.com/s/1BNHt_9fiqRPGmEXPaxaFXw)
- 将解压后的 `checkpoints_mlt/` 放到源码根目录下
- 运行demo：`python demo/demo.py`

# 参考
+ https://github.com/eragonruan/text-detection-ctpn/
+ https://arxiv.org/abs/1609.03605
