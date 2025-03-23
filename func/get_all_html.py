import math

import requests

video_num = 300
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
        html += response.text
    return html

html = get_search_results_html()
print(html)