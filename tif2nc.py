import argparse
import os
import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio import crs
from osgeo import gdal
import netCDF4 as nc
import re
import sys

# 下采样
def average_pooling(input_map,scale):

    # input_map sizes
    in_row,in_col = np.shape(input_map)
    # output_map sizes
    out_row,out_col = int(np.floor(in_row/scale)),int(np.floor(in_col/scale))
    row_remainder,col_remainder = np.mod(in_row,scale),np.mod(in_col,scale)
    if row_remainder != 0:
        out_row +=1
    if col_remainder != 0:
        out_col +=1
    output_map = np.zeros((out_row,out_col))

    # padding
    temp_map = np.lib.pad(input_map, ((0,scale-row_remainder),(0,scale-col_remainder)), 'edge')

    # average pooling
    for r_idx in range(0,out_row):
        for c_idx in range(0,out_col):
            startX = c_idx * scale
            startY = r_idx * scale
            poolField = temp_map[startY:startY + scale, startX:startX + scale]
            pool_out = np.nanmax(poolField)
            output_map[r_idx,c_idx] = pool_out
    return  output_map

# 命令行传参
parser = argparse.ArgumentParser(description='change tif to nc')
parser.add_argument('--variable', '-v', help='variable name',required=True)
parser.add_argument('--input_file_url', '-i', help='tif file path',required=True)
parser.add_argument('--scale','-s',help='scale of tif and nc,default: 1',default=1)
parser.add_argument('--output_file_url', '-o', help="nc file path,default: re.sub('rawdata','ncfiledata',input_file_url)")
parser.add_argument('--max_value','-m',help='The Upper Limit of Normal Value of variable,default: 1e10',default=1e10)
args = parser.parse_args()

# 处理传参
max_value = float(args.max_value)
scale = int(args.scale)
if re.search(r'.*\.tif$',args.input_file_url):
    input_file_url = args.input_file_url
    input_file_path = re.sub(r'(?<=/)[^/]+\.tif$','',input_file_url)
    input_file_name = re.findall(r'(?<=/)[^/]+\.tif$',input_file_url)[0]

else:
    sys.stderr.write("Invalid input_file_url")
    exit(1)

try:
    if args.output_file_url:
        output_file_url = args.output_file_url
    else:
        output_file_url = re.sub(r'\.tif$',r'.nc',input_file_url)
    output_file_path = re.sub(r'(?<=/)[^/]+\.[^/]+$','',output_file_url)
    output_file_name = re.findall(r'(?<=/)[^/]+\..*$',output_file_url)[0]
except Exception:
    sys.stderr.write("Invalid output_file_url")
    exit(1)

os.chdir(input_file_path)

# 转为地理坐标系WGS84
dst_crs = crs.CRS.from_epsg('4326')

with rasterio.open(input_file_name) as src_ds:
    profile = src_ds.profile

    # 计算在新空间参考系下的仿射变换参数，图像尺寸
    dst_transform, dst_width, dst_height = calculate_default_transform(
        src_ds.crs, dst_crs, src_ds.width, src_ds.height, *src_ds.bounds)

    # 更新数据集的元数据信息
    profile.update({
        'crs': dst_crs,
        'transform': dst_transform,
        'width': dst_width,
        'height': dst_height,
        'nodata': 0
    })

    if not os.path.exists(output_file_path):
        os.makedirs(output_file_path)
    os.chdir(output_file_path)

    # 重投影并写入数据
    with rasterio.open('temp.tif', 'w', **profile) as dst_ds:
        for i in range(1, src_ds.count + 1):
            src_array = src_ds.read(i)
            dst_array = np.empty((dst_height, dst_width), dtype=profile['dtype'])
            reproject(
                # 源文件参数
                source=src_array,
                src_crs=src_ds.crs,
                src_transform=src_ds.transform,
                # 目标文件参数
                destination=dst_array,
                dst_transform=dst_transform,
                dst_crs=dst_crs,
                # 其它配置
                resampling=Resampling.cubic,
                num_threads=2)

            dst_ds.write(dst_array, i)

gdal.AllRegister()
dataset=gdal.Open("temp.tif")       #打开文件
adfGeoTransform = dataset.GetGeoTransform()

longitude = adfGeoTransform[0]
latitude = adfGeoTransform[3]

im_width = dataset.RasterXSize    #栅格矩阵的列数
im_height = dataset.RasterYSize   #栅格矩阵的行数

longitude2 = longitude + (im_width-1) * adfGeoTransform[1] + (im_height-1) * adfGeoTransform[2]
latitude2 = latitude + (im_width-1) * adfGeoTransform[4] + (im_height-1) * adfGeoTransform[5]

im_data = dataset.ReadAsArray(0,0,im_width,im_height) #将数据写成数组，对应栅格矩阵
im_data[(im_data <= 1e-5) | (im_data >= max_value)] = np.nan #过滤异常值
if scale != 1:
    im_data = average_pooling(im_data,scale)
im_data[np.isnan(im_data)] = -9999

lonS = np.linspace(longitude,longitude2,im_width)[::scale]
latS = np.linspace(latitude,latitude2,im_height)[::scale]

dataset = None

da = nc.Dataset(output_file_name,'w',format='NETCDF4')
da.createDimension('lon',lonS.size)  #创建坐标点
da.createDimension('lat',latS.size)  #创建坐标点

da.createVariable("lon",'float',("lon"))  #添加coordinates
da.createVariable("lat",'float',("lat"))    #添加coordinates

da.variables['lat'][:]=latS     #填充数据
da.variables['lon'][:]=lonS    #填充数据

da.createVariable(args.variable,'float',('lat','lon'))   #创建变量
da.variables[args.variable][:] = im_data      #填充数据
da.close

# 删除临时文件
os.remove("temp.tif")
print(output_file_url)