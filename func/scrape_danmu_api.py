import requests
import re
import json
#
header = {
    "Cookie": "CURRENT_FNVAL=4048; browser_resolution=1431-795; header_theme_version=CLOSE; home_feed_column=5; bp_video_offset_387248104=838207007460687880; b_lsid=51BDA6410_18A6A32AAF7; PVID=2; DedeUserID=387248104; DedeUserID__ckMd5=997de6fe2948299f; SESSDATA=239fa927%2C1709550596%2Cd94d4%2A91; bili_jct=2500da9ad1627b694375b1f02b18c9ef; sid=7xmh2q46; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2OTQyNTc2MTcsImlhdCI6MTY5Mzk5ODQxNywicGx0IjotMX0.q63iI2yYkLp-E9hrqegvlSbfaH5ZMYJHdBX6CyFBJsI; bili_ticket_expires=1694257617; rpdid=|(Ju|YumJmlR0J'uYmJmm)Rul; buvid4=BBDA4179-43B6-BC97-2921-C3DA6C8BA41113675-023090619-CCD6quuR79vFz4HsddQmBw%3D%3D; buvid_fp=72144dcd920cccffdf5490b3588f77a7; _uuid=F277DA65-ADFA-7DDF-FA210-F9373AB795A413451infoc; b_nut=1693998413; b_ut=7; buvid3=DC452482-78AD-B786-8D0E-D798D1DCCCD013189infoc; i-wanna-go-back=-1",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
    "origin": "https://bilibili.com"
}
# 设置视频页面的URL

url = 'https://api.bilibili.com/x/v2/dm/web/history/seg.so?type=1&oid=1253529510&date=2023-09-04'

# 发送HTTP请求获取网页内容
response = requests.get(url, headers=header)

print(response.text)
danmaku_info = re.findall(".*?([\u4E00-\u9FA5]+).*?", response.text)
print(danmaku_info)
for danmu in danmaku_info:
    # print(danmu)
    # mode='a'追加写入 mode='w'覆盖写入
    with open('弹幕.txt', mode='a', encoding='utf-8') as f:
        f.write(danmu)
        f.write('\n')

