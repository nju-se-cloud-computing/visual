import glob
import csv
import time

from flask import Flask, render_template
from pymongo import MongoClient
from pyecharts import options as opts
from pyecharts.charts import Bar, Pie, WordCloud

'''
    从mongodb读取数据，将数据展现在前端

'''

uri = "mongodb+srv://Frank:123456789shi@cluster0.2hsme.gcp.mongodb.net/<Homework>?retryWrites=true&w=majority"
dbname = 'Homework'
readCol = 'visual_data'
line_index = 0

# 获取日期
with open('data/一般零售/SH600280-1148334872-1138334820kline.csv') as f1:
    r = csv.reader(f1)
    time_column = [row[0] for row in r]

# 存从数据库获取的数据
data = {}

'''
    将时间戳转换成日期，yyyy-mm-dd
'''


def timeStamp(time_num):
    time_ = float(time_num / 1000)
    time_array = time.localtime(time_)
    other_style_time = time.strftime("%Y-%m-%d", time_array)
    return other_style_time


app = Flask(__name__, static_folder="templates")


# 获取当天日期
def get_date():
    return timeStamp(int(time_column[line_index]))


''' 
    读mongo
    输入：字典。格式：{'module': '航空运输','time': '2019-08-09'}
    返回：多个字典

'''


def readFromMongo(dic):
    client = MongoClient(uri)
    dblist = client.list_database_names()
    if "Homework" in dblist:
        print("数据库已找到！")
    db = client[dbname]
    collection = db[readCol]

    doc = collection.find(dic)
    array = []
    for x in doc:
        array.append(x)
    return array[0]


def docClean(doc, module, date):
    max = -1
    for item in doc:
        if (str(item['data']) == date and item['module'] == module):
            temp = int(str(item['_id'])[0:8], 16)
            if (temp > max):
                max = temp

    for x in doc:
        if int(str(x['_id'])[0:8], 16) == max and str(x['data']) == date and x['module'] == module:
            print({'module': x['module'], 'time': x['data'], 'numerator': x['numerator']})
            return {'module': x['module'], 'time': x['data'], 'numerator': x['numerator']}


# 生产bar图像
def bar_base() -> Bar:
    global data
    data = readFromMongo({"date": get_date()})
    print(data)
    c = (
        Bar()
            .add_xaxis(data['modules'])
            .add_yaxis("上涨股票数", data['ups'], stack="stack1")
            .add_yaxis("下跌股票数", data['downs'], stack="stack1")
            .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
            .set_global_opts(
            title_opts=opts.TitleOpts(title=get_date() + "不同板块股票涨跌数柱状图"),
            yaxis_opts=opts.AxisOpts(name="股票数量"),
            xaxis_opts=opts.AxisOpts(name="板块名"),
            datazoom_opts=[opts.DataZoomOpts(), opts.DataZoomOpts(type_="inside")],

        )
    )
    pie = (
        Pie()
            .add(
            series_name="涨跌占比",
            data_pair=[
                ["总上涨数", data['number_ups']],
                ["总下跌数", data['number_downs']],

            ],
            center=["65%", "25%"],
            radius="20%",
        )
            .set_series_opts(tooltip_opts=opts.TooltipOpts(is_show=True, trigger="item"))
    )

    return c.overlap(pie)


# 生成word_cloud图像
def world_cloud() -> WordCloud:
    c = (
        WordCloud()
            .add(
            "",
            data['word_cloud'],
            word_size_range=[20, 100],
            textstyle_opts=opts.TextStyleOpts(),
        )
            .set_global_opts(title_opts=opts.TitleOpts(title=get_date() + "板块涨幅词云图"))
    )
    return c


@app.route("/")
def index():
    return render_template("index.html")


# 获取某日板块股票涨跌数柱状图
@app.route("/barChart")
def get_bar_chart():
    global line_index
    line_index += 1
    c = bar_base()
    return c.dump_options_with_quotes()


# 获取word_cloud
@app.route("/cloudChart")
def get_cloud_chart():
    c = world_cloud()
    return c.dump_options_with_quotes()


if __name__ == "__main__":
    app.run()
