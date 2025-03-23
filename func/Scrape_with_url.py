import math
import requests
import re
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from tqdm import tqdm
import pandas as pd
import jieba
import wordcloud
import imageio
from PIL import Image

barrages_num = 20  # 单个视频爬取弹幕数
video_num = 300  # 爬取视频数
pagenum = 0

ua = UserAgent()
headers = {
    "cookie": "buvid3=07FA5E6E-CF61-CA9F-14BC-26E1431C7AED73100infoc; b_nut=1681104373; _uuid=B7627B10B-91026-858E-CDED-BB10C110F86E3C75340infoc; CURRENT_FNVAL=4048; CURRENT_PID=388a3330-d79a-11ed-ac3d-19b01d09cd74; rpdid=0zbfvUppcs|nfndbSU9|1R8|3w1PLQwx; buvid_fp_plain=undefined; nostalgia_conf=-1; buvid4=A056DD55-235B-665A-5A92-5AB345FF7EDB78859-023041013-2P++RL08QGmsQngzsdizqQ==; hit-new-style-dyn=1; i-wanna-go-back=-1; b_ut=5; home_feed_column=5; hit-dyn-v2=1; FEED_LIVE_VERSION=V8; header_theme_version=CLOSE; fingerprint=9cb6844e0be9bf5daf511ea8b2512066; buvid_fp=9cb6844e0be9bf5daf511ea8b2512066; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2OTQyNjQwMzcsImlhdCI6MTY5NDAwNDgzNywicGx0IjotMX0.-2dV_z_lALgWjpupF44crOIqJ-PNsylftyrkyewfI5s; bili_ticket_expires=1694264037; CURRENT_QUALITY=80; PVID=5; bp_video_offset_387248104=838565679935258627; browser_resolution=1440-764; b_lsid=6FEF7AD3_18A6F86ABE5; SESSDATA=11523713,1709641562,68619*92; bili_jct=b91edfffe40bf3727e3833cdb941735b; DedeUserID=387248104; DedeUserID__ckMd5=997de6fe2948299f; sid=o408ajnw",
    'origin': 'https://www.bilibili.com',
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
    "referer": "https://t.bilibili.com/?spm_id_from=333.337.0.0",
}


def get_search_results_html():
    page, html = 1, ''
    url = "https://search.bilibili.com/all?keyword=日本核污染水排海&order=click"
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
        "Cookie": "buvid3=2F38CD55-CCD9-0D05-EFAC-D78F4FCEE3A133631infoc; b_nut=1691060433; i-wanna-go-back=-1; _uuid=E37F628D-CE5A-5DD1-B23C-910B92326A76633722infoc; FEED_LIVE_VERSION=V8; header_theme_version=CLOSE; SESSDATA=d324dcc4%2C1706612493%2C8ce13%2A81zqyFrgt0rrTutbzOcf6NXii0x3EXBwvDIT9w6zs4rXoM6miWp779yNngwMbCD26szHztpgAAEgA; bili_jct=348a40f9dff0f5a035a9bec3dd91083c; DedeUserID=520029018; DedeUserID__ckMd5=179dfa6087c5f3f9; rpdid=|(mmJlY|~||0J'uYmu|Y|Rm); buvid4=0A6B4ED8-EFBE-C823-919F-2D38E9352F7055238-023020811-AYMpmfEzGjyejvuh2eCCkA%3D%3D; buvid_fp_plain=undefined; nostalgia_conf=-1; b_ut=5; is-2022-channel=1; LIVE_BUVID=AUTO1116911562759162; CURRENT_QUALITY=116; hit-new-style-dyn=1; hit-dyn-v2=1; CURRENT_BLACKGAP=0; fingerprint=d1f57f19105afe876875f4d406cae4a6; CURRENT_FNVAL=4048; home_feed_column=5; browser_resolution=1699-953; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2OTQxODU1MTIsImlhdCI6MTY5MzkyNjMxMiwicGx0IjotMX0.gFAVbUppg5H_wIZGERddzOAdrhwXERwn1ImjtxkE2AY; bili_ticket_expires=1694185512; PVID=3; buvid_fp=d1f57f19105afe876875f4d406cae4a6; b_lsid=12A610B5C_18A68640A2F; sid=6ocelinu; bp_video_offset_520029018=837948252620849161"
    }
    for page in range(math.ceil(video_num / 30)):
        cur_url = url + "&page=" + str(page)
        response = requests.get(cur_url, headers=header)
        if (response.status_code == 200):
            print(f"第{page}页爬取成功!")
        else:
            print(f"第{page}页爬取失败...")
        html += response.text
    return html


def get_video_links(html):
    soup = BeautifulSoup(html, "html.parser")
    bvids = re.findall(r'bvid:"([^"]+)"', html)
    video_links = []
    for vid in bvids:
        video_links.append("https://www.bilibili.com/video/" + vid)
    return video_links


def get_info(vid):
    url = f"https://api.bilibili.com/x/web-interface/view/detail?bvid={vid}"
    response = requests.get(url)
    response.encoding = "utf-8"
    data = response.json()
    info = {}
    info["标题"] = data["data"]["View"]["title"]
    info["总弹幕数"] = data["data"]["View"]["stat"]["danmaku"]
    info["视频数量"] = data["data"]["View"]["videos"]
    info["cid"] = [dic["cid"] for dic in data["data"]["View"]["pages"]]
    if info["视频数量"] > 1:
        info["子标题"] = [dic["part"] for dic in data["data"]["View"]["pages"]]
    for k, v in info.items():
        print(k + ":", v)
    return info


def get_danmu(info):
    all_dms = []
    for i, cid in enumerate(info["cid"]):
        url = f"https://api.bilibili.com/x/v1/dm/list.so?oid={cid}"
        response = requests.get(url)
        response.encoding = "utf-8"
        data = re.findall('<d p="(.*?)">(.*?)</d>', response.text)
        dms = [d[1] for d in data]
        if info["视频数量"] > 1:
            print("cid:", cid, "弹幕数:", len(dms), "子标题:", info["子标题"][i])
        all_dms += dms
    print(f"共获取弹幕{len(all_dms)}条！")
    return all_dms


def save_danmu(bv_matches):
    for vid in bv_matches:
        info = get_info(vid)
        danmu = get_danmu(info)
        with open("../日本排放核污水弹幕.txt", "a", encoding="utf-8") as fout:
            for dm in danmu:
                fout.write(dm + "\n")


def get_bvs(links):
    bv_nuumbers = []
    for link in links:
        bv_pattern = r'/video/([A-Za-z0-9]+)'
        bv_match = re.search(bv_pattern, link)
        if bv_match:
            bv_number = bv_match.group(1)
            bv_nuumbers.append(bv_number)
            # print(bv_number)
    return bv_nuumbers


def txt_to_csv():
    df = pd.read_csv("../日本排放核污水弹幕.txt", delimiter="\t");
    df.to_csv("test.csv", encoding="utf-8", index=False)


def statistics():
    chunksize = 10000  # 每次读取的块大小
    value_counts = pd.Series(dtype=int)
    csv_name = "test.csv"
    save_name = "result.csv"
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


def generate_wordcloud():
    img = Image.open(r'../monster.png')
    f = open('../日本排放核污水弹幕.txt', encoding='utf-8')
    text = f.read()

    text_list = jieba.lcut(text)
    string = ''.join(text_list)

    # 词云图设置
    font = f'/System/Library/Fonts/Supplemental/Songti.ttc'
    wc = wordcloud.WordCloud(
        width=1800,
        height=1200,
        background_color='white',
        font_path=font,  # 设置字体 微软雅黑
        scale=15,
        stopwords={"省流"},
        mask=img,
        contour_width=50,
        contour_color='red',
    )

    wc.generate(string)
    wc.to_file('out.png')


def main():
    html = ''  # 存储对应页面返回的html
    keyword = "日本核污染水排海"
    for page in range(0, 30):
        html += get_search_results_html(page, keyword)
    # html = get_search_results_html()
    links = get_video_links(html)
    bvs = get_bvs(links)
    save_danmu(bvs)
    txt_to_csv()
    statistics()
    generate_wordcloud()


if __name__ == "__main__":
    main()