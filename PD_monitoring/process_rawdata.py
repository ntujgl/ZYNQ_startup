import pandas as pd
from sklearn.cluster import KMeans
import numpy as np
import os
import json

def uint14_to_int14(val):
    """Convert a 14-bit unsigned integer to a signed integer。"""
    if val & (1 << 13):  # If the sign bit (14th bit) is set
        return val - (1 << 14)  # Convert to negative
    return val  # Already positive

def convert_file(input_file, output_file):
    """Convert specific columns in the input file to signed integers and save the result."""
    with open(input_file, 'r') as f:
        lines = f.readlines()  # Read file line by line
    
    

    # 删除所有空行，并删除第一行有数据的行
    lines = [line for line in lines if line.strip()]  # 移除空行
    first_row_values = lines[0].split()
    if all(val == "-1" for val in first_row_values):  
        print("Warning: First row contains only '-1', No data collected .")
        return -1  # 第一行全是 -1，数据无效    

    lines = lines[1:]  # 删除第一行有数据的行

    converted_lines = []

    # Process each line, removing the first column and keeping the rest
    for line in lines:
        values = line.split()

        if len(values) > 4:  # Ensure the line has enough values to process
            # 1. Convert the 2nd to the (n-5)th columns (uint14 to int14 conversion)
            converted_values = []

            for val in values[1:-4]:  # Convert 2nd to (n-5)th column
                converted_values.append(str(uint14_to_int14(int(val))))

            # 2. The last four columns remain unchanged
            converted_values += values[-4:]  # Append the last four columns as-is

            # Join the converted values into a string and add it to the list of lines
            converted_lines.append(' '.join(converted_values))

    # Write the converted lines to the output file, keeping line breaks
    with open(output_file, 'w') as f:
        f.write('\n'.join(converted_lines))
    return 0  # 成功


def process_file(input_file, output_waveform_file,K,C):
    """Process the converted file, extract columns, and save them."""
    # 读取文件，使用正则表达式 '\s+' 匹配任意数量的空白字符作为分隔符
    df = pd.read_csv(input_file, sep=r'\s+', header=None)

    # 提取第2列到倒数第5列，并保存为 CSV
    df_extracted = df.iloc[:, 1:-4]  # 第2列到倒数第5列（Python索引从0开始）
    df_extracted = df_extracted/8191*0.875
    df_extracted = df_extracted*K+C
    
    # 获取每行的最后一个值
    last_values = df_extracted.iloc[:, -1]  # 选择每一行的最后一列的值

    # 添加该值到 DataFrame 的末尾
    # df_extracted['last_value'] = last_values
    
    # df_extracted.to_csv(output_waveform_file, sep='\t',index=False, header=False)
    # df_extracted.to_csv(output_waveform,index=False, header=False)
    # print(f"Data extracted and saved to {output_waveform_file}")
    return df_extracted


def convert_to_28bit(high_14bit, low_14bit):
    """Convert high and low 14-bit values to a 28-bit integer."""
    return (high_14bit << 14) | low_14bit

def calculate_phase_in_degrees(phase_value, period_value):
    """Calculate the phase in degrees based on the period."""
    if period_value == 0:
        print("Warning: Period value is zero. Skipping phase calculation.")
        return float('nan')  # 返回 NaN 表示无法计算
    result = (phase_value / period_value) * 360
    if result > 360:
        result -= 360
    return result

def process_phase_period(input_file, output_file,K,C):
    """处理文件的最后四列，计算相位和周期，并找到前几列每行的最大绝对值"""
    df = pd.read_csv(input_file, sep=r'\s+', header=None)

    # 提取第一列到倒数第五列
    first_to_fifth_last_columns = df.iloc[:, :-4]
    transformed_columns = (first_to_fifth_last_columns / 8191 * 0.875) * K + C
    # 计算每一行的绝对值最大值

    # 对每一行，找到绝对值最大的那个点的原始值（保留符号）
    max_values_per_row = transformed_columns.apply(lambda row: row.loc[row.abs().idxmax()], axis=1)
    # max_values_per_row = max_values_per_row/8191*0.875
    # max_values_per_row = max_values_per_row*K+C
    # 提取最后四列
    last_four_columns = df.iloc[:, -4:]
    results = []

    # 对于每一行，计算 phase 和 period
    for index, row in last_four_columns.iterrows():
        phase_high = int(row.iloc[0])  # 使用 iloc 按位置索引
        phase_low = int(row.iloc[1])
        period_high = int(row.iloc[2])
        period_low = int(row.iloc[3])

        # 合并高低14位为28位整数
        phase_value = convert_to_28bit(phase_high, phase_low)
        period_value = convert_to_28bit(period_high, period_low)

        # 计算 phase/period * 360
        phase_in_degrees = calculate_phase_in_degrees(phase_value, period_value)

        # 将结果存储到结果列表中，加入该行对应的最大绝对值
        results.append([max_values_per_row .iloc[index],  phase_in_degrees])

    # 将结果存储为 DataFrame
    # 将结果存储为 DataFrame
    results_df = pd.DataFrame(results)

    # 转置 DataFrame
    transposed_results_df = results_df.T
    transposed_results_df = transposed_results_df
    # 保存转置后的结果到文件，且不写入列名或索引
    # transposed_results_df.to_csv('prpd.csv', index=False, header=False)
    # transposed_results_df.to_csv(output_file, sep='\t',index=False, header=False)
    return transposed_results_df


def waveform_cluster_fft(waveform_data, k):
    """
    Perform KMeans clustering on the FFT results of waveform data.

    Parameters:
    waveform_data (DataFrame): The waveform data as a Pandas DataFrame.
    k (int): The number of clusters for KMeans.

    Returns:
    tuple: A tuple containing the cluster labels and the fitted KMeans model.
    """
    # 将 DataFrame 转换为 numpy 数组
    waveform_array = waveform_data.to_numpy()

    # 计算每一行波形的 FFT 幅度（仅保留正频部分）
    fft_results = np.abs(np.fft.fft(waveform_array, axis=1))[:, :waveform_array.shape[1] // 2]

    # 初始化 KMeans 模型
    kmeans = KMeans(n_clusters=k, random_state=0)

    # 使用 FFT 的幅度作为特征进行聚类
    labels = kmeans.fit_predict(fft_results)

    # 返回聚类标签和 KMeans 模型
    return labels

def save_clustered_waveforms_and_prpd(waveform_data, prpd_data, labels, output_dir):

    # Convert PRPD data to NumPy for easy indexing
    prpd_array = prpd_data.to_numpy()

    # Group data by cluster label
    unique_clusters = np.unique(labels)
    for cluster in unique_clusters:
        # Select waveforms and PRPD indices for this cluster
        cluster_indices = np.where(labels == cluster)[0]

        # Extract waveforms and PRPD data for the cluster
        cluster_waveforms = waveform_data.iloc[cluster_indices]
        cluster_prpd = prpd_array[:, cluster_indices]

        # Save waveforms to a file
        waveform_output_file = os.path.join(output_dir, f'waveform_cluster_{cluster}.csv')
        cluster_waveforms.to_csv(waveform_output_file, sep='\t', index=False, header=False)

        # Save PRPD data to a file
        prpd_output_file = os.path.join(output_dir, f'prpd_cluster_{cluster}.csv')
        pd.DataFrame(cluster_prpd).to_csv(prpd_output_file, sep='\t', index=False, header=False)

        print(f"Saved waveform cluster {cluster} to {waveform_output_file}")
        print(f"Saved PRPD cluster {cluster} to {prpd_output_file}")

def read_waveform_and_prpd(waveform_file, prpd_file):

    try:
        # 读取 waveform 数据
        waveform_data = pd.read_csv(waveform_file, sep='\t', header=None)
        print(f"Loaded waveform data from {waveform_file}, shape: {waveform_data.shape}")

        # 读取 PRPD 数据
        prpd_data = pd.read_csv(prpd_file, sep='\t', header=None)
        if prpd_data.shape[0] != 2:
            raise ValueError(f"PRPD file must have exactly 2 rows. Found {prpd_data.shape[0]} rows.")
        print(f"Loaded PRPD data from {prpd_file}, shape: {prpd_data.shape}")

        return waveform_data, prpd_data
    except Exception as e:
        print(f"Error reading waveform or PRPD files: {e}")
        return None, None

def ai_cluster_gen(labels, pd_type=None, optimal_cluster=None, default_index=None):
    # 确保 labels 是列表类型
    labels_list = list(labels) if isinstance(labels, np.ndarray) else labels
    
    if pd_type is None:
        # 默认情况下，所有类型设置为 "unknown"
        unique_labels = set(labels_list)
        pd_type = {str(label): "unknown" for label in unique_labels}
    
    if optimal_cluster is None:
        # 如果未提供 optimal_cluster，默认为唯一标签数量
        optimal_cluster = len(set(labels_list))
    
    if default_index is None:
        # 如果未提供 default_index，选择每个 cluster 中的第一个样本
        default_index = {str(label): (labels_list.index(label) if label in labels_list else -1) for label in set(labels_list)}
    
    # 转换所有非 JSON 兼容数据类型
    pd_type = {str(k): str(v) for k, v in pd_type.items()}  # 确保 pd_type 的值是字符串
    default_index = {str(k): int(v) for k, v in default_index.items()}  # 确保 default_index 的值是整数
    
    # 构造字典数据
    ai_cluster_dict = {
        "status": "ok",
        "label": list(map(int, labels_list)),  # 确保 labels 是整数列表
        "pd_type": pd_type,
        "optimal cluster": int(optimal_cluster),  # 确保 optimal_cluster 是整数
        "default_index": default_index
    }
    
    return ai_cluster_dict

def save_ai_cluster_to_json(ai_cluster_dict, file_path="ai_cluster.json"):

    try:
        with open(file_path, "w") as json_file:
            json.dump(ai_cluster_dict, json_file, indent=4)
        print(f"AI cluster data saved to {file_path}")
    except Exception as e:
        print(f"Error saving AI cluster data to JSON: {e}")

if __name__ == "__main__":
    waveform_data,prpd_data=read_waveform_and_prpd("/home/xilinx/PD_monitoring/Testdata/waveform.csv","/home/xilinx/PD_monitoring/Testdata/prpd.csv")
    labels=waveform_cluster_fft(waveform_data, 3)  
    save_clustered_waveforms_and_prpd(waveform_data, prpd_data, labels, "/home/xilinx/PD_monitoring/Testdata")
    ai_cluster_dict=ai_cluster_gen(labels)
    # print(ai_cluster_dict)
    save_ai_cluster_to_json(ai_cluster_dict,"/home/xilinx/PD_monitoring/Testdata/sensor-ai-cluster.json")