import re
import requests
import pandas as pd
import time
from tqdm import trange

# 视频页面点击“浏览器地址栏小锁-Cookie-bilibili.com-Cookie-SESSDATA”进行获取
SESSDATA = ""
# 视频页面“按F12-Console-输入document.cookie”进行获取
cookie = ""
cookie += f";SESSDATA={SESSDATA}"
headers = {
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
    "Cookie": "CURRENT_FNVAL=4048; b_lsid=B782DBA7_18A6D268FA2; browser_resolution=1440-795; header_theme_version=CLOSE; home_feed_column=5; innersign=0; hit-new-style-dyn=1; PVID=5; bp_video_offset_387248104=838207007460687880; DedeUserID=387248104; DedeUserID__ckMd5=997de6fe2948299f; SESSDATA=239fa927%2C1709550596%2Cd94d4%2A91; bili_jct=2500da9ad1627b694375b1f02b18c9ef; sid=7xmh2q46; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2OTQyNTc2MTcsImlhdCI6MTY5Mzk5ODQxNywicGx0IjotMX0.q63iI2yYkLp-E9hrqegvlSbfaH5ZMYJHdBX6CyFBJsI; bili_ticket_expires=1694257617; rpdid=|(Ju|YumJmlR0J'uYmJmm)Rul; buvid4=BBDA4179-43B6-BC97-2921-C3DA6C8BA41113675-023090619-CCD6quuR79vFz4HsddQmBw%3D%3D; buvid_fp=72144dcd920cccffdf5490b3588f77a7; _uuid=F277DA65-ADFA-7DDF-FA210-F9373AB795A413451infoc; b_nut=1693998413; b_ut=7; buvid3=DC452482-78AD-B786-8D0E-D798D1DCCCD013189infoc; i-wanna-go-back=-1",
}


def get_info(vid):
    url = f"https://api.bilibili.com/x/web-interface/view/detail?bvid={vid}"
    response = requests.get(url, headers=headers)
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


def get_danmu(info, start, end):
    date_list = [i for i in pd.date_range(start, end).strftime("%Y-%m-%d")]
    all_dms = []
    for i, cid in enumerate(info["cid"]):
        dms = []
        for j in trange(len(date_list)):
            url = f"https://api.bilibili.com/x/v2/dm/web/history/seg.so?type=1&oid={cid}&date={date_list[j]}"
            response = requests.get(url, headers=headers)
            response.encoding = "utf-8"
            data = re.findall(r"[:](.*?)[@]", response.text)
            dms += [dm[1:] for dm in data]
            time.sleep(3)
        if info["视频数量"] > 1:
            print("cid:", cid, "弹幕数:", len(dms), "子标题:", info["子标题"][i])
        all_dms += dms
    print(f"共获取弹幕{len(all_dms)}条！")
    return all_dms

def main():
    vid = input("输入视频编号: ")
    info = get_info(vid)
    start = input("输入弹幕开始时间（年-月-日）: ")
    end = input("输入弹幕结束时间（年-月-日）: ")
    danmu = get_danmu(info, start, end)
    with open("danmu.txt", "w", encoding="utf-8") as fout:
        for dm in danmu:
            fout.write(dm + "\n")


if __name__ == "__main__":
    main()
