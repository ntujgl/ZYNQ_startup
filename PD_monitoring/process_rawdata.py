import pandas as pd

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

def process_file(input_file, output_waveform_file,K,C):
    """Process the converted file, extract columns, and save them."""
    # 读取文件，使用正则表达式 '\s+' 匹配任意数量的空白字符作为分隔符
    df = pd.read_csv(input_file, sep=r'\s+', header=None)

    # 提取第2列到倒数第5列，并保存为 CSV
    df_extracted = df.iloc[:, 1:-4]  # 第2列到倒数第5列（Python索引从0开始）
    df_extracted = df_extracted/1000
    df_extracted = df_extracted*K+C
    df_extracted.to_csv(output_waveform_file, sep='\t',index=False, header=False)
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

    # 计算每一行的绝对值最大值

    # 对每一行，找到绝对值最大的那个点的原始值（保留符号）
    max_values_per_row = first_to_fifth_last_columns.apply(lambda row: row.loc[row.abs().idxmax()], axis=1)
    max_values_per_row = max_values_per_row/1000
    max_values_per_row = max_values_per_row*K+C
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
    transposed_results_df.to_csv(output_file, sep='\t',index=False, header=False)
    return transposed_results_df

if __name__ == "__main__":
    # File paths for input and output
    input_file_original = 'rawdata.txt' 
    output_waveform = 'waveform.csv'  # Output for waveform data
    output_prpd = 'prpd.csv'  # Output for PRPD data
    converted_file = 'converted_pddata.txt'  # 保存转换后的文件
    convert_file(input_file_original, converted_file)
    # Step 1: Generate waveform data
    process_file(converted_file, output_waveform)

    # Step 2: Generate PRPD data
    process_phase_period(converted_file, output_prpd)