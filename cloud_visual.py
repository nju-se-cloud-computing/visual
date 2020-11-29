import glob
import csv
import time

from PIL.ImageQt import rgb
from flask import Flask, render_template
from pymongo import MongoClient
from pyecharts import options as opts
from pyecharts.charts import Bar, Pie, WordCloud, Line

'''
    从mongodb读取数据，将数据展现在前端

'''

uri = "mongodb+srv://Frank:123456789shi@cluster0.2hsme.gcp.mongodb.net/<Homework>?retryWrites=true&w=majority"
dbname = 'Homework'
readCol = 'visual_data'
read_numerator = 'test5'
line_index = 0
circul_all = {}

# 获取日期
with open('data/一般零售/SH600280-1148334872-1138334820kline.csv') as f1:
    r = csv.reader(f1)
    time_column = [row[0] for row in r]

# 存从数据库获取的数据
data = {}
latestId = 0

#

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


def readFromMongo(dic, read):
    client = MongoClient(uri)
    dblist = client.list_database_names()
    if "Homework" in dblist:
        print("数据库已找到！")
    db = client[dbname]
    collection = db[read]

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


'''
    获取板块发行量
'''


def get_circul_data():
    csv_path = "data/"
    modules_path = glob.glob("{}/*".format(csv_path))
    for module in modules_path:
        circul_sum = 0  # 发行量的和
        module_name = module[5:]
        shares_path = glob.glob("{}/*.csv".format(module))
        # 模块中股票的处理
        for share in shares_path:
            circulation = int(share.split('-')[1])  # 股票的发行量
            circul_sum += circulation
        circul_all[module_name] = circul_sum


get_circul_data()


# 生产bar图像
def bar_base() -> Bar:
    global data
    data = readFromMongo({"date": get_date()}, readCol)
    print(data)
    c = (
        Bar()
            .add_xaxis(data['modules'])
            .add_yaxis("上涨股票数", data['ups'], stack="stack1")
            .add_yaxis("下跌股票数", data['downs'], stack="stack1")
            .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
            .extend_axis(
            yaxis=opts.AxisOpts(
                name="上涨股票占比率",
                type_="value",
                min_=0,
                max_=100,
                interval=10,
                axislabel_opts=opts.LabelOpts(formatter="{value} %"),
            )
        )
            .set_global_opts(
            title_opts=opts.TitleOpts(title=get_date() + "不同板块股票涨跌数柱状图"),
            yaxis_opts=opts.AxisOpts(name="股票数量"),
            xaxis_opts=opts.AxisOpts(name="板块名", is_show=True),
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
            center=["75%", "25%"],
            radius="20%",
        )
            .set_series_opts(tooltip_opts=opts.TooltipOpts(is_show=True, trigger="item"))
    )
    rate = []
    for i in range(len(data['ups'])):
        rate.append(round(data['ups'][i] * 100 / (data['ups'][i] + data['downs'][i])))

    line = (
        Line()
            .add_xaxis(xaxis_data=data['modules'])
            .add_yaxis(
            series_name="上涨股票占比率（百分数）",
            yaxis_index=1,
            y_axis=rate,
            label_opts=opts.LabelOpts(is_show=False),
            linestyle_opts=opts.LineStyleOpts(width=2),
            is_smooth=True,
        )
    )

    return c.overlap(pie).overlap(line)


# 生成word_cloud图像
def world_cloud() -> WordCloud:
    for i in range(len(data['word_cloud'])):
        data['word_cloud'][i][1] = round(data['word_cloud'][i][1], 2)
        if data['word_cloud'][i][0][0:2] == "其他":
            data['word_cloud'][i][1] = -100.00

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


def readLatest():
    client = MongoClient(uri)
    dblist = client.list_database_names()
    if "Homework" in dblist:
        print("数据库已找到！")
    db = client[dbname]
    collection = db[read_numerator]

    doc = collection.find({'module': '半导体', 'data': '2019-08-09'})

    docarray = []
    for x in doc:
        global latestId
        dic = {}
        id = int(str(x['_id'])[0:8], 16)
        if id > latestId:
            latestId = id
            dic['module'] = x['module']
            dic['date'] = x['data']
            dic['numerator'] = x['numerator']
            docarray.append(dic)
    print(latestId)
    return docarray


def bar_ups_and_downs() -> Bar:
    # 这里要改成不断获取最新数据的函数
    real_datas = readLatest()
    print("real_datas:")
    print(real_datas)
    update_data = {}

    for i in range(len(circul_all)):
        update_data[data['modules'][i]] = 0

    for i in range(len(real_datas)):
        real_data = real_datas[i]
        up_and_down_data = round((float(real_data['numerator']) / circul_all[real_data['module']]), 2)
        update_data[real_data['module']] = up_and_down_data

    bar_data = []

    for i in range(len(circul_all)):
        if update_data[data['modules'][i]] == 0:
            bar_data.append(0)
        else:
            bar_data.append(update_data[data['modules'][i]])
    print(bar_data)
    if real_datas == []:
        c = (
            Bar()
                .add_xaxis(data['modules'])
                .add_yaxis("实时获取的股票涨幅", bar_data)
                .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
                .set_global_opts(
                title_opts=opts.TitleOpts(title="实时获取板块股票涨跌幅柱状图"),
                yaxis_opts=opts.AxisOpts(name="股票涨跌幅"),
                xaxis_opts=opts.AxisOpts(name="板块名", is_show=True),
                # datazoom_opts=[opts.DataZoomOpts(), opts.DataZoomOpts(type_="inside")],
            )
        )
    else:
        c = (
            Bar()
                .add_xaxis(data['modules'])
                .add_yaxis("实时获取的股票涨幅", bar_data)
                .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
                .set_global_opts(
                title_opts=opts.TitleOpts(title=real_data['date'] + " 实时获取板块股票涨跌幅柱状图"),
                yaxis_opts=opts.AxisOpts(name="股票涨跌幅"),
                xaxis_opts=opts.AxisOpts(name="板块名", is_show=True),
                # datazoom_opts=[opts.DataZoomOpts(), opts.DataZoomOpts(type_="inside")],
            )
        )
    return c


@app.route("/")
def index():
    return render_template("index.html")


# 传送某日板块股票涨跌数柱状图
@app.route("/barChart")
def get_bar_chart():
    global line_index
    line_index += 1
    c = bar_base()
    return c.dump_options_with_quotes()


# 传送word_cloud
@app.route("/cloudChart")
def get_cloud_chart():
    c = world_cloud()
    return c.dump_options_with_quotes()


# 传送实时获取板块涨幅条形图
@app.route("/bar_ups")
def get_ups_and_downs_chart():
    c = bar_ups_and_downs()
    return c.dump_options_with_quotes()


if __name__ == "__main__":
    app.run()
