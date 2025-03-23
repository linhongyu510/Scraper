import requests
from bs4 import BeautifulSoup
import re

#head为请求头，将代码伪装成浏览器访问目标服务器
head = {
    "Cookie": "CURRENT_FNVAL=4048; browser_resolution=1431-795; header_theme_version=CLOSE; home_feed_column=5; bp_video_offset_387248104=838207007460687880; b_lsid=51BDA6410_18A6A32AAF7; PVID=2; DedeUserID=387248104; DedeUserID__ckMd5=997de6fe2948299f; SESSDATA=239fa927%2C1709550596%2Cd94d4%2A91; bili_jct=2500da9ad1627b694375b1f02b18c9ef; sid=7xmh2q46; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2OTQyNTc2MTcsImlhdCI6MTY5Mzk5ODQxNywicGx0IjotMX0.q63iI2yYkLp-E9hrqegvlSbfaH5ZMYJHdBX6CyFBJsI; bili_ticket_expires=1694257617; rpdid=|(Ju|YumJmlR0J'uYmJmm)Rul; buvid4=BBDA4179-43B6-BC97-2921-C3DA6C8BA41113675-023090619-CCD6quuR79vFz4HsddQmBw%3D%3D; buvid_fp=72144dcd920cccffdf5490b3588f77a7; _uuid=F277DA65-ADFA-7DDF-FA210-F9373AB795A413451infoc; b_nut=1693998413; b_ut=7; buvid3=DC452482-78AD-B786-8D0E-D798D1DCCCD013189infoc; i-wanna-go-back=-1",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
    "origin": "https://bilibili.com"
}

def get_response(html_url, video_url):
    head["referer"] = video_url
    response = requests.get(html_url, headers=head)
    if response.status_code == 200:
        return response
    else:
        print("请求失败")


def get_date(html_url):
    response = get_response(html_url, video_url)
    json_data = response.json()
    date = json_data['data']
    print(date)
    return date


def get_head(video_url):
    # B站视频的URL
    url = video_url

    # 发送HTTP请求获取页面内容
    response = requests.get(url)

    # 检查响应状态码
    if response.status_code == 200:
        # 使用BeautifulSoup解析页面内容
        soup = BeautifulSoup(response.text, 'html.parser')

        # 查找视频标题元素，通常在meta标签中
        title_element = soup.find('meta', {'name': 'title'})

        # 提取视频标题
        if title_element:
            video_title = title_element['content']
            # print(f'视频标题: {video_title}')
            return video_title
        else:
            print('未找到视频标题')
    else:
        print('无法访问该页面')


def save(contents):
    headline = get_head(video_url)
    for content in contents:
        with open(f'{headline}弹幕.txt', mode='a', encoding='utf-8') as f:
            f.write(content)
            f.write('\n')
            print(content)


def save_date(contents, date):
    headline = get_head(video_url)
    for content in contents:
        with open(f'{headline}弹幕({date}).txt', mode='a', encoding='utf-8') as f:
            f.write(content)
            f.write('\n')
            print(content)


def main(html_url):
    data = get_date(html_url)
    for date in data:
        day_url = f"https://api.bilibili.com/x/v2/dm/web/history/seg.so?type=1&oid=1245133831&date={date}"
        day_url1 = f"https://api.bilibili.com/x/v2/dm/web/history/seg.so?type=1&oid=1253529510&date={date}"
        html_data = get_response(day_url1, video_url).text
        result = re.findall(".*?([\u4E00-\u9FA5]+).*?", html_data)
        save(result)

if __name__ == '__main__':
    index_url = "https://api.bilibili.com/x/v2/dm/history/index?month=2023-09&type=1&oid=1245133831"
    index_url2 = "https://api.bilibili.com/x/v2/dm/history/index?month=2023-09&type=1&oid=1253529510"
    video_url = "https://www.bilibili.com/video/BV1yF411C7ZJ"
    video_url2 = "https://www.bilibili.com/video/BV1t94y147Fk"
    main(index_url)
    # geturl()
