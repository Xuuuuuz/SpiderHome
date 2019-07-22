#coding=utf-8
_date_ = '2019/7/18 14:58'

import requests
import pymysql

requests.packages.urllib3.disable_warnings()
from lxml import etree
import time
import random
from multiprocessing.dummy import Pool
import re



# from multiprocessing.dummy import Pool
# 获取京东商品详情页
class jd():
    def __init__(self):
        self.main_url = "https://item.jd.com/{}.html"
        self.user_agents = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1"
        self.proxy_url = ''  #代理池
        #数据库信息
        #self.kind=''
        #self.db=pymysql.connect(host='',
        #                        user='',
        #                       password='',
        #                        database='',
        #                        charset='',
        #                        port='')
        #self.cursor=self.db.cursor()
        self.n = 0

    # 解析前半页
    def parse_index(self, url):
        try:
            headers = {'User-Agent': self.user_agents}
            proxies = self.get_a_proxy()
            response = requests.get(url, headers=headers, verify=False, timeout=15,proxies=proxies)
            # 以网页编码方式解码
            response.encoding = response.apparent_encoding
            time.sleep(random.randint(1, 2))
            # print(response.text)
            if response.status_code == 200:
                return response.text
            else:
                return None
        except Exception as E:
            # print(str(E))
            return None

    # 通过首前半页获取商品详情页url(只有一半的商品url，后半段是通过异步加载的方式加载)；获取商品data-pid，构造后半段商品url
    def get_goods_url(self, response):
        pre_goods_url_list = []
        if response:
            html = etree.HTML(response)
        else:
            print('前半页爬取失败')
            return
        products = html.xpath('//ul[@class="gl-warp clearfix"]/li')
        for product in products:
            goods_dic = {}
            goods_name = ''.join(product.xpath('.//div[@class="p-name p-name-type-2"]/a/em/text()')).strip().replace(
                ' ', '')
            goods_href = product.xpath('.//div[@class="p-img"]/a/@href')[0]
            goods_id = re.search('(\d+)',goods_href).group()
            goods_dic['goods'] = goods_name
            goods_dic['goods_href'] = goods_id
            # print(goods_dic)
            self.parse_item(goods_dic)
            #self.coll.insert_one(dict(goods_dic))
        # 获取前30个商品的data-pid
        goods_pid_list = html.xpath("//li[@class='gl-item']")
        if goods_pid_list:
            goods_pid = [goods_pid.get('data-pid') for goods_pid in goods_pid_list]
            # print(goods_pid,len(goods_pid))
            return goods_pid, pre_goods_url_list
            # 获取网页中后半商品的url

    def get_a_proxy(self):
        res = requests.get(self.proxy_url).text

        proxies = {
            "http": "http://{}".format(res),
        }
        return proxies

    def get_other_goods_url(self, pid, url):
        #获取后半段的商品
        print(url)
        page = int(url[117:])
        # print(page)
        other_goods_url_list = []
        other_url = "https://search.jd.com/s_new.php?keyword=%E7%94%B7%E8%A3%85&enc=utf-8&qrst=1&rt=1&stop=1&vt=2&wq=%E7%94%B7%E8%A3%85&page={}&s=31&scrolling=y&log_id={}&tpl=3_M&show_items={}"
        # 时间戳去掉后两位
        linux_sec = str(time.time())[:-2]
        # 构造后半部分网页，有三处要除以一个page+1，一处是log_id为时间戳去掉后两位，最后的一堆列表是前半部分解析的data-pid构成的
        other_url = other_url.format(str(page + 1), linux_sec, ','.join(pid))
        ref = 'https://search.jd.com/Search?keyword=%E7%94%B7%E8%A3%85&enc=utf-8&qrst=1&rt=1&stop=1&vt=2&wq=%E7%94%B7%E8%A3%85&page={}'.format(
                str(page))
        headers = {
            # refer必须带，表示又前一网页跳转过来
            'referer': ref.strip(),
            'User-Agent': random.choice(self.user_agents)
        }
        proxies = self.get_a_proxy()
        r = requests.get(url=other_url, headers=headers, verify=False, timeout=15,proxies=proxies)
        print(other_url)
        r.encoding = r.apparent_encoding
        response = r.text
        html = etree.HTML(response)
        products = html.xpath('//li[@class="gl-item"]')
        for product in products:
            goods_dic = {}
            goods_name = ''.join(product.xpath('.//div[@class="p-name p-name-type-2"]/a/em/text()')).strip().replace(
                ' ', '')
            goods_href = product.xpath('.//div[@class="p-img"]/a/@href')[0]
            goods_id = re.search('(\d+)', goods_href).group()
            goods_dic['goods'] = goods_name
            goods_dic['goods_href'] = goods_id
            # print(goods_dic)
            # print('------')
            self.parse_item(goods_dic)
        print("获取后半商品url成功")


    def parse_item(self,goods_dic):
        self.n+=1
        print(self.n)
        goods_id=goods_dic['goods_href']
        url = self.main_url.format(goods_id)
        del goods_dic['goods_href']
        headers = {'User-Agent': self.user_agents}
        rule_dict = {"版型": "", "面料": "", "风格": "", "适用场景": "", "图案主题": "", "材质": "", "适用季节": "", "领型": "", "袖长": "",
                     "工艺": "", "厚度": "", "基础风格": "", "适用人群": "", "商品产地": "", "上市时间": "", "流行元素": "", "图案": ""}
        #rule_dict = {"type": "", "material": "", "style": "", "case": "", "pattern": "", "quality": "", "season": "", "collar": "", "sleeve": "",
        #             "craft": "", "land": "", "basic": "", "people": "", "place": "", "time": "", "element": "", "design": ""}
        proxies = self.get_a_proxy()
        r = requests.get(url=url, headers=headers, verify=False, timeout=15,proxies=proxies)
        response = r.text

        products = etree.HTML(response)

        ruler = re.compile(".*colorSize: \[(.*?)\],.*", re.S)
        try:
            result = re.findall(ruler, response)[0]
            results = list(eval(result))
            s = set()
            try:
                for tip in results:
                    s.add(tip['颜色'])
            except:
                pass


            for i in products.xpath('//ul[@class="parameter2 p-parameter-list"]/li/text()'):
                i = i.split('：')
                if i[0] in rule_dict:
                    rule_dict[i[0]] = i[1]
            rule_dict_new = {"type": "版型", "material": "面料", "style": "风格", "cases": "适用场景", "pattern": "图案主题", "quality": "材质",
                         "season": "适用季节", "collar": "领型", "sleeve": "袖长",
                         "craft": "工艺", "land": "厚度", "basic": "基础风格", "people": "适用人群", "place": "商品产地", "time": "上市时间",
                         "element": "流行元素", "design": "图案"}
            for k, v in rule_dict_new.items():
                rule_dict_new[k] = rule_dict[v]
            good=dict(rule_dict_new,**goods_dic)
            good['color']=','.join(list(s))
            good['web']='京东'

            self.into_sql(good)
        except:
            pass

    def into_sql(self,data):
        time.sleep(1)
        # print(data)
        try:
            keys=','.join(data.keys())
            values=','.join(['%s']*len(data))
            sql='INSERT INTO %s (%s) VALUES (%s)' % (self.kind,keys,values)
            self.cursor.execute(sql, tuple(data.values()))
            self.db.commit()
            self.db.ping(True)
            print(data['goods']+'插入成功')
        except Exception as e:
            print(data['goods']+'已经存在')


def main(url):
    response = jd.parse_index(url)
    goods_pid, pre_goods_url_list = jd.get_goods_url(response)
    jd.get_other_goods_url(pid=goods_pid, url=url)
    time.sleep(5)
    # jd.get_all_goods_url_list(pre_goods_url_list,other_goods_url_list)



if __name__ == '__main__':
    jd = jd()
    url = 'https://search.jd.com/Search?keyword=%E7%94%B7%E8%A3%85&enc=utf-8&qrst=1&rt=1&stop=1&vt=2&wq=%E7%94%B7%E8%A3%85&page={}'
    for i in range(1, 200, 2):
        time.sleep(8)
        format_url=url.format(str(i))
        main(format_url)

    print("数据爬取完毕")