# 转换tif和grb2文件为nc的脚本
## 运行环境

- 系统版本：ubuntu20.04
- python版本：Python 3.8.2
- GCC版本： [GCC 9.3.0] on linux
- pyproj 没有 windws 库，不要尝试在 windows 上运行

## 依赖的安装

依次执行：
```bash
sudo apt install libeccodes-dev
pip3 install numpy
pip3 install pyproj
pip3 install eccodes-python
pip3 install pygrib
pip3 install falsk
pip3 install geos
sudo apt install libffi-dev
sudo apt install libgdal-dev
pip3 install netCDF4
pip3 install pygdal(先检查gdal的版本设置(如：gdal-config --version，输出3.0.4)，
    然后在安装同样版本(如pip3 install pygdal==3.0.4.6，没有3.0.4，可取其后更小版本))
pip3 install rasterio
```

## docker
- 因为需要输出文件，故直接挂载磁盘到docker dockerfile中并未复制脚本到的docker中
1. 构建镜像
```bash
docker build -f dockerfile -t gdal .
```
2. 启动docker
```bash
docker run -v [本地目录]:[需要挂载目录] --name=gdal -itd gdal
```
3. 调用脚本
```bash
docker exec -i gdal python3 [脚本路径] [参数]
```