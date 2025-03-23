import jieba
import wordcloud
import imageio

img = imageio.imread('monster.png')

f = open('./日本排放核污水弹幕.txt', encoding='utf-8')
text = f.read()

text_list = jieba.lcut(text)
string = ''.join(text_list)
# print(string)

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