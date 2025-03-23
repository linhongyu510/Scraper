import requests
from bs4 import BeautifulSoup
import re

head = {
    "Cookie": "CURRENT_FNVAL=4048; browser_resolution=1431-795; header_theme_version=CLOSE; home_feed_column=5; bp_video_offset_387248104=838207007460687880; b_lsid=51BDA6410_18A6A32AAF7; PVID=2; DedeUserID=387248104; DedeUserID__ckMd5=997de6fe2948299f; SESSDATA=239fa927%2C1709550596%2Cd94d4%2A91; bili_jct=2500da9ad1627b694375b1f02b18c9ef; sid=7xmh2q46; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2OTQyNTc2MTcsImlhdCI6MTY5Mzk5ODQxNywicGx0IjotMX0.q63iI2yYkLp-E9hrqegvlSbfaH5ZMYJHdBX6CyFBJsI; bili_ticket_expires=1694257617; rpdid=|(Ju|YumJmlR0J'uYmJmm)Rul; buvid4=BBDA4179-43B6-BC97-2921-C3DA6C8BA41113675-023090619-CCD6quuR79vFz4HsddQmBw%3D%3D; buvid_fp=72144dcd920cccffdf5490b3588f77a7; _uuid=F277DA65-ADFA-7DDF-FA210-F9373AB795A413451infoc; b_nut=1693998413; b_ut=7; buvid3=DC452482-78AD-B786-8D0E-D798D1DCCCD013189infoc; i-wanna-go-back=-1",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
    "origin": "https://bilibili.com",
    # "referer": "https://search.bilibili.com/all?vt=05151524&keyword=%E6%97%A5%E6%9C%AC%E6%A0%B8%E6%B1%A1%E6%9F%93%E6%B0%B4%E6%8E%92%E6%B5%B7&from_source=webtop_search&spm_id_from=333.788&search_source=3",
}
# 定义要爬取的URL
# url = "https://search.bilibili.com/all?keyword=%E6%97%A5%E6%9C%AC%E6%A0%B8%E6%B1%A1%E6%9F%93%E6%B0%B4%E6%8E%92%E6%B5%B7&from_source=webtop_search&spm_id_from=333.788&search_source=3"
url = "https://search.bilibili.com/all?vt=88934835&keyword=%E6%97%A5%E6%9C%AC%E6%8E%92%E6%94%BE%E6%A0%B8%E6%B1%A1%E6%B0%B4&page=3&o=60"
# 发送HTTP请求获取页面内容
response = requests.get(url, headers=head)
# print(response.text)

# 使用Beautiful Soup解析页面
soup = BeautifulSoup(response.text, "html.parser")

video_links = []
for link in soup.find_all("a"):
    video_url = link.get("href")
    if video_url != None:
        # pattern = r"\/video\/(BV\w+)\/"
        # match = re.search(pattern, url)
        # if match:

        # if video_url != video_links[-1]:
            if "BV" in video_url:
                video_links.append(video_url[2:])

# 打印所有视频链接
i = 0
for link in video_links:
    i += 1
    print(f"{link} + {i}")

url1 = video_links[0]
response = requests.get(url1, headers=head)
print(response.text)
