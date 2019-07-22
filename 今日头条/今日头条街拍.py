#coding=utf-8
_date_ = '2019/4/4 21:16'
import time
from urllib.parse import urlencode
import requests
from hashlib import md5
import os
from multiprocessing.pool import Pool

def get_page(offset):
    """
    构造get请求参数
    :param offset:页码
    :return: json数据
    """
    timestamp = int(time.time() * 1000)
    params= {
        'app_name':'web_search',
        'offset':offset,
        'keyword':'街拍',
        'timestamp':timestamp
    }
    base_url = 'https://www.toutiao.com/api/search/content/?'
    url = base_url + urlencode(params)
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
    except:
            return None

def get_image(json):
    """
    json解析获取标题和内容
    :param json:
    :return:
    """
    if json.get('data'):
        for item in json.get('data'):
            title = item.get('title')
            images = item.get('image_list')
            yield {
                'title':title,
                'images':images,
            }


def save_image(item):
    """
    保存照片，去重
    :param item: 照片参数
    :return:
    """
    if not os.path.exists('images/{}'.format(item.get('title'))):
        os.mkdir('images/{}'.format(item.get('title')))
    try:
        for images in item.get('images'):
            response = requests.get(url=images.get('url'))
            if response.status_code == 200:
                file_path = 'images/{0}/{1}.{2}'.format(item.get('title'),
                                                 md5(response.content).hexdigest(),
                                                 'jpg')
                if not os.path.exists(file_path):
                    with open(file_path,'wb') as f:
                        f.write(response.content)
                else:
                    print('已存在',file_path)
    except requests.ConnectionError:
        print('保存失败')

def main(offset):
    """
    调用函数
    :param offset: 页码
    :return:
    """
    json = get_page(offset)
    for item in get_image(json):
        print(item)
        save_image(item)

GROUP_START = 1
GROUP_END = 20

if __name__ == '__main__':
    #实例化线程池
    pool = Pool()
    group = [x*20 for x in range(GROUP_START,GROUP_END+1)]
    #传入参数
    pool.map(main,group)
    pool.close()
    pool.join()