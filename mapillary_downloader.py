#encoding:utf-8
import requests
import os
import json
from bs4 import BeautifulSoup
import datetime
import  MySQLdb
datetime_format = '%Y-%m-%d %H:%M:%S'


def get_coor_list(lat_min,lat_max,lon_min,lon_max):
    area = []
    lat = lat_min
    while lat <lat_max :
        lon = lon_min
        while lon <lon_max :
            coordinate = (lat,lon)
            area.append(coordinate)
            lon +=0.05
        lat += 0.05
    return area

def get_city_coor(city):
    #city = 'london'
    handle = open('./config/city_list.txt')
    for line in handle:
        if '\xef' in line:
            line = line.replace('\xef\xbb\xbf','')
        buf = line.split()
        if buf[0] == city:
            coor_list = get_coor_list(float(buf[1]),float(buf[2]),float(buf[3]),float(buf[4]))
            #print coor_list
    handle.close()
    return coor_list

def get_start_date():
    date_file = open('./config/date_config.json')
    start_time  = date_file.read()
    start_time = json.loads(start_time)
    start_time = start_time['start_time']
    #print start_time
    date_file.close()
    dt = datetime.datetime.strptime(start_time, datetime_format)
    #print dt.day
    date = {}
    date['year'] = str(dt.year)
    date['day'] = str(dt.day)
    date['month'] = str(dt.month)
    date['start_time'] = start_time
    return date
def get_download_time(date,day_delta):
    #date = get_start_date()
    start_time = date['start_time']
    download_time = []
    #datetime_format = '%Y-%m-%d %H:%M:%S'
    #start_time='2013-06-27 00:00:00'
    #min_date = time.mktime(time.strptime(start_time, datetime_format))
    #covert_time.append(int(min_date))
    day = datetime.datetime.strptime(start_time, datetime_format)
    delta = datetime.timedelta(days=day_delta)
    n_day = day + delta
    download_time.append(day)
    download_time.append(n_day)
    return download_time

def save_url(img_url,file_name):
    handle = open(file_name,'a+')
    handle.write(img_url)
    handle.write('\n')
    handle.close()

def add_one_week(start_day,day_delta):
    start_day = date['start_time']
    #print start_day,type(start_day)
    day = datetime.datetime.strptime(start_day, datetime_format)
    delta = datetime.timedelta(days=day_delta)
    next_day = day + delta
    next_day = next_day.strftime(datetime_format)
    #print next_day,type(next_day)
    refresh = {}
    refresh['start_time'] = next_day
    #print refresh
    handle = open('./config/date_config.json','w+')
    handle.write(json.dumps(refresh))
    handle.close()



if __name__ == '__main__':
    db = MySQLdb.connect('localhost','root','5#611','Mapillary')
    cs = db.cursor()
    #database has been connected
    city = 'london'
    last_weeks = 2
    day_delta = 7
    coor_list = get_city_coor(city)
    area_index = 1
    while last_weeks > 0:
        date = get_start_date()
        print u'==============正在抓取日期：%s ==============' % (date['start_time'].split(' ')[0])
        datapath = './data/' + date['year'] + '/' + date['month'] + '/' + date['day']
        if os.path.isdir(datapath):
            filename = datapath + '/' + city + '.txt'
        else:
            os.makedirs(datapath)
            filename = datapath + '/' + city + '.txt'
        download_time = get_download_time(date,day_delta)
        print download_time
        start_time = download_time[0].isoformat()
        end_time = download_time[1].isoformat()
        for i in coor_list:
            print '----抓取%s第 %d 区域----' % (city, area_index)
            area_index += 1
            lon = str(i[1])
            lat = str(i[0])
            # print lon,type(lon),lat
            url = 'https://a.mapillary.com/v3/images?client_id=ekcyWUdPNnkwSlRrMThjMVhWTFV0dzphYjRiMmE0MzM3YzQzMTAy&lookat=%s,%s&closeto=%s,%s&start_time=%s&end_time=%s&radius=2775'
            url = url % (lon, lat, lon, lat, start_time, end_time)
            print url
            res = requests.get(url)
            soup = BeautifulSoup(res.text, 'html.parser')
            dic = json.loads(soup.text)
            image_URL_L = 'https://d1cuyjsrcm0gby.cloudfront.net/'
            image_URL_R = '/thumb-1024.jpg'
            if len(dic['features']) > 0:
                for info in dic['features']:
                    key = info['properties']['key']
                    coor = info['geometry']['coordinates']
                    lon = coor[0]
                    lat = coor[1]
                    image_URL = image_URL_L + key + image_URL_R
                    #save_url(image_URL, filename)
                    cs.execute("insert into image values(%s,%s,%s,%s)", (key, lat, lon,image_URL))
                    db.commit()
                    # print image_URL+' '+str(lon)+','+str(lat)
            else:
                print '(%s,%s)----no features----' % (lat, lon)
        last_weeks -= 1
        if last_weeks == 1:
            area_index = 1
        add_one_week(date['start_time'],day_delta)
        # 图片URL格式https://d1cuyjsrcm0gby.cloudfront.net/gBTh9zUYu3YhHqhgBiZUqw/thumb-1024.jpg

    '''
    #下载图片
    #img = requests.get(image_URL)
    #f = open('..\\test111.jpg','ab')
    #f.write(img.content)
    #f.close()
    '''
