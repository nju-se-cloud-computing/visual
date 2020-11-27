import glob
import csv
import time

from flask import Flask, render_template

from pyecharts import options as opts
from pyecharts.charts import Bar, Pie, WordCloud

# 获取bar的数据
csv_path = "data/"
modules_path = glob.glob("{}/*".format(csv_path))
xaxis = []
column = []
for module in modules_path:
    xaxis.append(module[5:])
line_index = 0
with open('data/一般零售/SH600280-1148334872-1138334820kline.csv') as f1:
    r = csv.reader(f1)
    time_column = [row[0] for row in r]

# 获取world_cloud的数据
with open('weighted_chg_percent.csv') as f2:
    r2 = csv.reader(f2)
    for row in r2:
        modules = row[2:]
        break


def timeStamp(time_num):
    time_ = float(time_num / 1000)
    time_array = time.localtime(time_)
    other_style_time = time.strftime("%Y-%m-%d", time_array)
    return other_style_time


# 更新bar的数据
def update_ups_and_downs_bar(line_lidex):
    yaxis = []
    ups = []
    downs = []
    tmp = 0
    for module in modules_path:
        up = 0
        down = 0
        shares_path = glob.glob("{}/*.csv".format(module))
        for share in shares_path:
            with open(share) as f:
                reader = csv.reader(f)
                column = [row[6] for row in reader]
                if len(column) < 285: continue
            if column[line_lidex][0] == "-":
                down += 1
            else:
                up += 1
        ups.append(up)
        downs.append(down)
    yaxis.append(ups)
    yaxis.append(downs)
    return yaxis


# 更新word_cloud 数据
def update_word_cloud(line_index):
    words = []
    counter = 0
    with open('weighted_chg_percent.csv') as f2:
        r2 = csv.reader(f2)
        for row in r2:
            if counter == line_index:
                value = row[2:]
                break
            else:
                counter += 1
    for i in range(1,len(modules)):
        words.append((modules[i], float(value[i])))
    return words


app = Flask(__name__, static_folder="templates")


# 获取当天日期
def get_date():
    return timeStamp(int(time_column[line_index]))


# 生产bar图像
def bar_base(yaxis) -> Bar:
    c = (
        Bar()
            .add_xaxis(xaxis)
            .add_yaxis("上涨股票数", yaxis[0], stack="stack1")
            .add_yaxis("下跌股票数", yaxis[1], stack="stack1")
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
                ["总上涨数", sum(yaxis[0])],
                ["总下跌数", sum(yaxis[1])],

            ],
            center=["65%", "25%"],
            radius="20%",
        )
            .set_series_opts(tooltip_opts=opts.TooltipOpts(is_show=True, trigger="item"))
    )
    return c.overlap(pie)


# 生成word_cloud图像
def world_cloud(words) -> WordCloud:
    c = (
        WordCloud()
            .add(
            "",
            words,
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
    yaxis = update_ups_and_downs_bar(line_index)
    print(yaxis)
    c = bar_base(yaxis)
    return c.dump_options_with_quotes()


# 获取word_cloud
@app.route("/cloudChart")
def get_cloud_chart():
    words = update_word_cloud(line_index)
    c = world_cloud(words)
    print(words)
    return c.dump_options_with_quotes()


if __name__ == "__main__":
    app.run()
