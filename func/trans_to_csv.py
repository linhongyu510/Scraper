from tqdm import tqdm
import pandas as pd


def txt_to_csv():
    df = pd.read_csv("日本排放核污水弹幕.txt", delimiter="\t");
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

if __name__ == "__main__":
    txt_to_csv()
    statistics()
