import re
import requests
from multiprocessing.dummy import Pool
from tqdm import tqdm
import pandas as pd
import jieba
import wordcloud
import imageio

keyword = "日本核污染水排海"  # 用来存取要爬取b站的关键字
pagenum = 10  # 爬取的页码数量
danmu_num = 0  # 用来统计弹幕的数量
pool = Pool(6)  # 使用线程池来加快提保存弹幕的速度 【性能改进】

# 使用UA来将程序伪装成浏览器进行request请求
headers = {
    "cookie": "buvid3=07FA5E6E-CF61-CA9F-14BC-26E1431C7AED73100infoc; b_nut=1681104373; _uuid=B7627B10B-91026-858E-CDED-BB10C110F86E3C75340infoc; CURRENT_FNVAL=4048; CURRENT_PID=388a3330-d79a-11ed-ac3d-19b01d09cd74; rpdid=0zbfvUppcs|nfndbSU9|1R8|3w1PLQwx; buvid_fp_plain=undefined; nostalgia_conf=-1; buvid4=A056DD55-235B-665A-5A92-5AB345FF7EDB78859-023041013-2P++RL08QGmsQngzsdizqQ==; hit-new-style-dyn=1; i-wanna-go-back=-1; b_ut=5; home_feed_column=5; hit-dyn-v2=1; FEED_LIVE_VERSION=V8; header_theme_version=CLOSE; fingerprint=9cb6844e0be9bf5daf511ea8b2512066; buvid_fp=9cb6844e0be9bf5daf511ea8b2512066; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2OTQyNjQwMzcsImlhdCI6MTY5NDAwNDgzNywicGx0IjotMX0.-2dV_z_lALgWjpupF44crOIqJ-PNsylftyrkyewfI5s; bili_ticket_expires=1694264037; CURRENT_QUALITY=80; PVID=5; bp_video_offset_387248104=838565679935258627; browser_resolution=1440-764; b_lsid=6FEF7AD3_18A6F86ABE5; SESSDATA=11523713,1709641562,68619*92; bili_jct=b91edfffe40bf3727e3833cdb941735b; DedeUserID=387248104; DedeUserID__ckMd5=997de6fe2948299f; sid=o408ajnw",
    'origin': 'https://www.bilibili.com',
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
    "referer": "https://t.bilibili.com/?spm_id_from=333.337.0.0",
}


# 获取keyword对应页面的html
# 1. 拼接keyword和page成当前要爬取的页面的url
# 2. 使用requests的get方法获取当前页面的html
def get_search_results_html(page):
    # 调用b站搜索对应的api接口
    url = f"https://search.bilibili.com/all?keyword={keyword}&order=click"

    # 拼接当前所要获得的视频的url
    cur_url = url + "&page=" + str(page)

    # 使用requests获取当前url对应的html文件
    response = requests.get(cur_url, headers=headers)

    # 如果response的状态码为200，则说明get方法成功，返回html
    if (response.status_code == 200):
        return response.text
    # 如果response的状态码不是200，则说明获取当前url的html文件失败，打印输出失败
    else:
        print(f"获取第{page}页的html失败...")


# 使用正则表达式提取html中的全部bv号
def get_bvs(html):
    bvids = re.findall(r'bvid:"([^"]+)"', html)
    return bvids


# 使用b站的api获取bv号对应视频的标题、总弹幕数、视频数量和cid
def get_info(vid):
    # 使用vid拼接b站api获取视频信息的url
    url = f"https://api.bilibili.com/x/web-interface/view/detail?bvid={vid}"

    # 使用requests获得url对应的html文件
    response = requests.get(url)

    # 将编码格式设置为utf-8
    response.encoding = "utf-8"

    # 将response解析成json的形式，方便使用字典获取所需的数据
    data = response.json()

    # 使用字典的形式保存应视频的标题、总弹幕数、视频数量和cid
    info = {}
    info["标题"] = data["data"]["View"]["title"]
    info["总弹幕数"] = data["data"]["View"]["stat"]["danmaku"]
    info["视频数量"] = data["data"]["View"]["videos"]
    info["cid"] = [dic["cid"] for dic in data["data"]["View"]["pages"]]
    if info["视频数量"] > 1:
        info["子标题"] = [dic["part"] for dic in data["data"]["View"]["pages"]]
    # 用来测试打印当前视频的标题、总弹幕数、视频数量和cid
    # for k, v in info.items():
    #     print(k + ":", v)
    return info


# 1. 通过b站弹幕的api使用cid获取视频对应的弹幕的html文件
# 2. 使用正则表达式将html文件的中文句子提取出来

def get_danmu(info):
    # 定义变量来保存所有弹幕
    all_dms = []
    for i, cid in enumerate(info["cid"]):

        # 调用b站的api使用cid获取对应视频的弹幕的url
        url = f"https://api.bilibili.com/x/v1/dm/list.so?oid={cid}"

        # 使用requests获得对应url的html文件
        response = requests.get(url)

        # 将html文件的编码设置为utf-8
        response.encoding = "utf-8"

        # 使用正则表达式提取html文件中的弹幕信息
        data = re.findall('<d p="(.*?)">(.*?)</d>', response.text)

        # 提取弹幕的第一句
        dms = [d[1] for d in data]

        # 如果视频下有字标题则打印输出
        if info["视频数量"] > 1:
            print("cid:", cid, "弹幕数:", len(dms), "子标题:", info["子标题"][i])
        all_dms += dms

    # 输出当前视频爬取的弹幕数量
    print(f"获取弹幕{len(all_dms)}条！")
    return all_dms

# 保存获取的弹幕
def save_danmu(bv_matches):
    for vid in bv_matches:
        # 使用b站的api获取bv号对应视频的标题、总弹幕数、视频数量和cid使用b站的api获取bv号对应视频的标题、总弹幕数、视频数量和cid
        info = get_info(vid)

        # 提取出弹幕信息
        danmu = get_danmu(info)

        # 将弹幕保存到
        with open(f"./{keyword}弹幕.txt", "a", encoding="utf-8") as fout:
            for dm in danmu:
                fout.write(dm + "\n")


# 将弹幕文件转换为csv格式来统计弹幕数据
def txt_to_csv():
    df = pd.read_csv(f"{keyword}弹幕.txt", delimiter="\t");
    df.to_csv(f"{keyword}.csv", encoding="utf-8", index=False)


# 将csv文件转换成表格的形式统计数据便于后续的处理

def statistics():
    chunksize = 10000  # 每次读取的块大小
    value_counts = pd.Series(dtype=int)
    # 设置要转换的csv文件名
    csv_name = f"{keyword}.csv"
    # 设置转换后保存的csv的文件名
    save_name = f"{keyword}.csv"

    for chunk in tqdm(pd.read_csv(csv_name, dtype=str, chunksize=chunksize), total=1219):
        # 获取所有文本数据并统计每个值的重复次数
        counts = pd.Series(chunk.values.ravel()).value_counts()
        value_counts = value_counts.add(counts, fill_value=0)

    # 重置索引并按重复次数从高到低排序
    value_counts = value_counts.reset_index()
    value_counts.columns = ['弹幕', '重复次数']
    value_counts = value_counts.sort_values(by='重复次数', ascending=False)

    # 创建进度条
    pbar = tqdm(total=len(value_counts), desc='Processing')

    # 保存结果到新的CSV文件
    value_counts.to_csv(save_name, index=False)

    # 更新进度条
    pbar.update()

    # 关闭进度条
    pbar.close()

    # 输出消息
    print("已经去重完成！")

# 使用词云生成可视化图片
def generate_wordcloud():
    # 获取图片样式
    img = imageio.imread('monster.png')

    # 读取要做成词云图的数据
    f = open(f'./{keyword}弹幕.txt', encoding='utf-8')
    text = f.read()

    # 将弹幕数据切片
    text_list = jieba.lcut(text)
    string = ''.join(text_list)

    # 词云图设置
    font = f'/System/Library/Fonts/Supplemental/Songti.ttc'
    wc = wordcloud.WordCloud(
        width=1800,  # 设置宽度
        height=1200,  # 设置高度
        background_color='white',  # 设置背景颜色
        font_path=font,  # 设置字体 微软雅黑
        scale=15,  # 设置大小
        stopwords={"省流"},  # 设置禁止的词
        mask=img,  # 设置图片样式
        contour_width=50,  # 设置边缘宽度
        contour_color='red',  # 设置边缘颜色
    )

    # 生成词云图
    wc.generate(string)
    wc.to_file(f'{keyword}.png')


def main():
    # 存储对应页面返回的html
    html = ''

    # 获取pagenum数量的html
    for page in range(0, pagenum):
        html += get_search_results_html(page)

    # 从html中提取出全部的bvid
    bvs = get_bvs(html)

    # 将bvid切片，方便后续使用线程池
    bvss = [bvs[i:i + 10] for i in range(0, 10)]

    # 使用线程池来加快提保存弹幕的速度 【性能改进】
    pool.map(save_danmu, bvss)
    save_danmu(bvs)

    # 将保存的弹幕文件转换为csv文件
    txt_to_csv()

    # 使用表格来统计每个弹幕的重复次数
    statistics()

    # 将获取的弹幕用词云生成图片实现可视化
    generate_wordcloud()


if __name__ == "__main__":
    main()
