import nltk
from nltk import FreqDist
from nltk.tokenize import word_tokenize
import matplotlib.pyplot as plt
from wordcloud import WordCloud

# 下载NLTK的停用词数据
nltk.download('stopwords')

# 示例评论和弹幕数据
comments = [
    "保护地球！保护海洋！",
    "保护海洋！",
    "保护地球保护海洋",
    "保护地球！保护海洋！",
    "保护海洋！",
    "保护地球保护海洋",
    "保护海洋！保护地球！",
    "辐岛",
    "使徒来袭",
    "保护海洋！！！",
    "注意安全",
    "逆天",
    "《承诺》",
    "保护海洋！！！保护地球！！！",
    "保护海洋！！",
    "保护海洋！保护海洋！保护海洋！",
    "甲级战犯",
    "上热门",
    "众所周知，日本发明了最先进的核污染水处理技术，世界应该向日本学习",
    "保护海洋!",
    "支持",
    "666",
    "保护海洋！保护地球！保护海洋！保护地球！保护海洋！保护地球！保护海洋！保护地球！保护海洋！保护地球！保护海洋！保护地球！保护海洋！保护地球！保护海洋！保护地球！保护海洋！保护地球！保护海洋！保护地球！",
    "《辐岛》",
    "看完了",
    "保护海洋，保护地球",
    "保护海洋保护海洋保护海洋保护海洋保护海洋保护海洋保护海洋保护海洋",
    "1",
    "保护海洋！抵制日本！",
    "？",
    "哎",
    "保护地球保护海洋！保护地球保护海洋！保护地球保护海洋！",
    "保护海洋！保护海洋！保护海洋！保护海洋！保护海洋！",
    "罪人",
    "看看水颜色比第一天排水的时候黑多少啊",
    "EVA",
    "海洋是另外一个世界，是数以万计生物的家园！坚决保护海洋生态！坚决保护地球家园！保护海洋！保护海洋！保护海洋！保护海洋！保护海洋！保护海洋！保护海洋！保护海洋！保护海洋！保护海洋！保护海洋！保护海洋！海",
    "EVAの小曲",
    "全世界",
    "啊？",
    "保护海洋！保护海洋！保护海洋！保护海洋！",
    "——核污染水中的放射性核素可能多达千余种，有的无检测手段！",
    "卧槽",
    "海纳百氚",
    "全球",
    "保护地球",
    "百氚东倒海",
    "保护海洋，保护地球！",
    "上热门！",
    "畜生",
    "保护海洋！！！保护海洋！！！保护海洋！！！",
    "《最终没喝》",
    "《绝不》",
    "《可以饮用》",
    "团结起来，全球人应该全面禁止抵制日本所有物品",
    "保护海洋，人人有责！！！",
    "《safe》",
    "狼狈为奸",
    "日本没了可以，但是还我太平洋！",
    "有",
    "保护地球！",
    "保护地球保护海洋！！！",
    "人类补完计划",
    "畜牲",
    "坚决抵制日本排放核污染水",
    "《甲级战犯》",
    "注意安全！",
    "保护地球，保护海洋",
    "躬匠精神",
    "上热门！！！",
    "保护地球！！！保护海洋！！！",
    "说得好",
    "保护海洋！！！！！",
    "父慈子孝",
    "全人类的罪人",
    "世界可以没有日本，但不能没有海洋",
    "世界可以没有日本，但不能没有海洋！",
    "马扁",
    "水是剧毒的(确信)",
    "笑死",
    "使  徒  照  片",
]

# 将评论合并成一个文本字符串
text = " ".join(comments)

# 分词
tokens = word_tokenize(text)

# 去除停用词
stop_words = set(nltk.corpus.stopwords.words("chinese"))  # 使用中文停用词表
filtered_tokens = [word.lower() for word in tokens if word.isalnum() and word.lower() not in stop_words]

# 词频统计
freq_dist = FreqDist(filtered_tokens)

# 输出词频最高的前20个词
top_words = freq_dist.most_common(20)
for word, frequency in top_words:
    print(f"{word}: {frequency}")

# 制作词云图
wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)

# 可视化词云图
plt.figure(figsize=(10, 5))
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis("off")
plt.title("词云图")
plt.show()
