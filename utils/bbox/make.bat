python setup.py install

REM ===================================================
REM win10 + python35 编译的结果：
REM build\lib.win-amd64-3.5\bbox.cp35-win_amd64.pyd
REM build\lib.win-amd64-3.5\nms.cp35-win_amd64.pyd
REM ===================================================

mv build/lib.*/*.pyd ./
rm -rf build/