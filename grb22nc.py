import argparse
import os
import numpy
from osgeo import gdal
import netCDF4 as nc
import pygrib
import datetime as dt
import re
import sys
import json

def grb22nc(filename,input_file_path,output_file_path):
    os.chdir(input_file_path)
    out_filename_base = re.sub(r'_\d{12}_\d{5}\.GRB2$','',filename)
    grbs = pygrib.open(filename)
    grbs.seek(0)
    ## 逐三小时
    per_three_count=0 # 逐3小时次数
    per_three_value=[]

    ## 逐24小时
    per24_value=[]
    per24_tmp_datas=[]
    per24_tmp_name=[]
    per24_tmp_grb_name=[]
    per24_data=()

    ## 近几天
    per_day_count = 0
    per_day_value=[]
    per_day_data=()

    for grb in grbs:

        # 取经纬度数组
        lat,lon = grb.latlons()
        # 生成经纬度坐标点数组
        lonS = numpy.linspace(lon[0][0],lon[-1][-1],len(lon[0]))
        latS = numpy.linspace(lat[0][0],lat[-1][-1],len(lat))

        # 输出目录
        if not os.path.exists(output_file_path):
            os.mkdir(output_file_path)
        os.chdir(output_file_path)
        out_filename = out_filename_base + '_' + grb.validDate.strftime("%Y%m%d%H%M") + '.nc'
        # print(grb.validDate.strftime("%Y%m%d%H%M"))

        if per_three_count < 8:
            da = nc.Dataset(out_filename,'w',format='NETCDF4')
            da.createDimension('longitude',len(lon[0]))  #创建坐标点
            da.createDimension('latitude',len(lat))  #创建坐标点

            da.createVariable("longitude",'float64',("longitude"))  #添加coordinates
            da.createVariable("latitude",'float64',("latitude"))  #添加coordinates

            da.variables['longitude'][:]=lonS     #填充数据
            da.variables['latitude'][:]=latS      #填充数据

            da.createVariable(grb.name,'double',('latitude','longitude')) #创建变量
            da.variables[grb.name][:] = grb.values      #填充数据
            da.close
            per_three_value.append(out_filename)

        if per_three_count < 16:
            per24_tmp_datas.append(grb.values)
            per24_tmp_name.append('per24' + '_' + out_filename)
            per24_tmp_grb_name.append(grb.name)
        per_three_count += 1

        if len(per_day_data) == 0 :
            per_day_data = grb.values
        elif str(grb.validDate.strftime("%Y%m%d%H%M")).endswith('2000') and len(per_day_data) != 0:
            per_day_count +=1
            per_day_name = 'per' + '_' + str(per_day_count) + 'day' + '_' + out_filename
            daync = nc.Dataset(per_day_name,'w',format='NETCDF4')
            daync.createDimension('longitude',len(lon[0]))  #创建坐标点
            daync.createDimension('latitude',len(lat))  #创建坐标点

            daync.createVariable("longitude",'float64',("longitude"))  #添加coordinates
            daync.createVariable("latitude",'float64',("latitude"))  #添加coordinates

            daync.variables['longitude'][:]=lonS     #填充数据
            daync.variables['latitude'][:]=latS      #填充数据

            daync.createVariable(grb.name,'double',('latitude','longitude')) #创建变量
            daync.variables[grb.name][:] = per_day_data     #填充数据
            daync.close
            per_day_value.append(per_day_name)

            per_day_data = [grb.values,per_day_data]
            per_day_data = numpy.nansum(per_day_data,axis=0)
        else:
            per_day_data = [grb.values,per_day_data]
            per_day_data = numpy.nansum(per_day_data,axis=0)

    for index in range(8):
        per24_data = per24_tmp_datas[index]
        for data_index in range(index+1, index+8):
            per24_data = [per24_tmp_datas[data_index],per24_data]
            per24_data = numpy.nansum(per24_data,axis=0)

        # print(per24_data)

        per24nc = nc.Dataset(per24_tmp_name[index],'w',format='NETCDF4')
        per24nc.createDimension('longitude',len(lon[0]))  #创建坐标点
        per24nc.createDimension('latitude',len(lat))  #创建坐标点

        per24nc.createVariable("longitude",'float64',("longitude"))  #添加coordinates
        per24nc.createVariable("latitude",'float64',("latitude"))  #添加coordinates

        per24nc.variables['longitude'][:]=lonS     #填充数据
        per24nc.variables['latitude'][:]=latS      #填充数据

        per24nc.createVariable(per24_tmp_grb_name[index],'double',('latitude','longitude')) #创建变量
        per24nc.variables[per24_tmp_grb_name[index]][:] = grb.values      #填充数据
        per24nc.close
        per24_value.append(per24_tmp_name[index])
        # print(per24_tmp_name[index])
        per24_data=()

    jsondata = {}
    jsondata['per_three']=per_three_value
    jsondata['per_day']=per_day_value
    jsondata['per_24']=per24_value
    print(json.dumps(jsondata))





# 命令行传参
parser = argparse.ArgumentParser(description='change grib2 to nc')
parser.add_argument('--input_file_url', '-i', help='grib2 file path',required=True)
parser.add_argument('--output_file_path', '-o', help="nc file path,  default: same as grib2 file path")
args = parser.parse_args()

if re.search(r'^/.*?\.gri?b2$',args.input_file_url,re.IGNORECASE):
    input_file_url = args.input_file_url
    input_file_path = re.sub(r'(?<=/)[^/]+\.gri?b2$','',input_file_url,flags=re.IGNORECASE)
    input_file_name = re.findall(r'(?<=/)[^/]+\.gri?b2$',input_file_url,re.IGNORECASE)[0]
else:
    sys.stderr.write("Invalid input_file_url")
    exit(1)

if args.output_file_path == None:
    output_file_path = input_file_path
else:
    if re.search(r'^/(\w+/?)+$',args.output_file_path):
        output_file_path = args.output_file_path
    else:
        sys.stderr.write("Invalid output_file_path")
        exit(1)

grb22nc(input_file_name,input_file_path,output_file_path)