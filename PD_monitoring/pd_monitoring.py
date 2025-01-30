import os
import subprocess
import json
import configparser
import time
import shutil
import process_rawdata
import numpy as np
import pandas as pd
import paho.mqtt.client as mqtt

main_path = None

# MQTT 服务器配置
MQTT_BROKER = "20.188.124.61"
MQTT_PORT = 1883
MQTT_TOPIC = "python/mqtt/msgs"
MQTT_USERNAME = "user"
MQTT_PASSWORD = "1234"

LNA_PARAMS = {
    0: {"K": 3, "C": 0.015},
    1: {"K": 3 / 10, "C": 0.015 / 10},
    2: {"K": 3 / 110, "C": 0.015 / 110}
}

def send_mqtt_message(panel, extra_msg=""):
    client = mqtt.Client()  # 创建 MQTT 客户端
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)  # 设置用户名和密码

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)  # 连接 MQTT 服务器
        msg = f"S5 Ch{panel}: {extra_msg}".strip()  # 组合消息，去除多余空格
        print(f"Publishing MQTT Message: {msg}")

        client.publish(MQTT_TOPIC, msg)  # 发布 MQTT 消息
        client.disconnect()
        print("MQTT Message Sent Successfully!")

    except Exception as e:
        print(f"Failed to send MQTT message: {e}")

def get_lna_params(lna_number):
    """根据 lna_number 获取对应的 K 和 C 参数"""
    # 如果 lna_number 不在字典中，使用默认值 (3, 0.015)
    params = LNA_PARAMS.get(lna_number, {"K": 3, "C": 0.015})
    return params["K"], params["C"]


def load_kernel_module():
    """
    Load the kernel module needed for data acquisition.
    This function should be called once before the main loop.
    """
    ko_file_path = os.path.join(main_path, 'Program', 'adc-axi-dma.ko')
    try:
        print(f"Loading kernel module {ko_file_path}...")
        subprocess.run(['insmod', ko_file_path], check=True)
        print(f"Kernel module {ko_file_path} loaded successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to load kernel module {ko_file_path}: {e}")
        print("Continuing without exiting...")



def get_main_path():
    """ 
    Get the current working directory path at the time of program execution
    and assign it to the global variable main_path.
    :return: The absolute path of the current working directory.
    """
    global main_path
    main_path = os.getcwd()
    print("Main Path:",main_path)

def run_downloadsettings(panel_id):
    # Construct the path to the panel directory
    target_directory = os.path.join(main_path, 'DataTransfer', f'CH{panel_id}')

    # Construct the path to the executable in the DataTransfer directory
    executable_path = os.path.join(main_path, 'DataTransfer', 'goblobarm32_1204')

    # Change to the target directory
    os.chdir(target_directory)

    # Execute the command using the absolute path of the executable
    command = f'{executable_path} -downloadsettings'
    subprocess.run(command, shell=True)

    # Optionally, change back to the original directory
    os.chdir(main_path)

def run_uploaddata(panel_id):
    # Construct the path to the panel directory
    target_directory = os.path.join(main_path, 'DataTransfer', f'CH{panel_id}')

    # Construct the path to the executable in the DataTransfer directory
    executable_path = os.path.join(main_path, 'DataTransfer', 'goblobarm32_1204')

    # Change to the target directory
    os.chdir(target_directory)

    # Execute the command using the absolute path of the executable
    command = f'{executable_path} -uploaddata'
    subprocess.run(command, shell=True)

    # Optionally, change back to the original directory
    os.chdir(main_path)


def run_settingschanged(panel_id):
    """
    Execute the goblobarm32_1204 -settingschanged command and determine the return value.
    :param panel_id: The panel ID used to construct the directory path.
    """
    # Construct the path to the panel directory
    target_directory = os.path.join(main_path, 'DataTransfer', f'CH{panel_id}')

    # Construct the path to the executable in the DataTransfer directory
    executable_path = os.path.join(main_path, 'DataTransfer', 'goblobarm32_1204')

    # Change to the target directory
    os.chdir(target_directory)

    # Execute the command and capture the return value
    command = f'{executable_path} -settingschanged'
    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    # Print the output of the command
    output = result.stdout.strip()
    os.chdir(main_path)
    # Determine and print the result
    if output == "true":
        return True
    elif output == "false":
        return False
    else:
        print("ERROR! error message:", output)
        return None
        

    # Optionally, change back to the original directory
    


def read_settings_json(panel_id):
    """
    Read the settings.json file from the specified panel's directory.
    
    :param panel_id: The panel ID used to construct the directory path.
    :return: A dictionary containing the contents of the settings.json file.
    """
    # Construct the path to the panel's directory
    target_directory = os.path.join(main_path, 'DataTransfer', f'CH{panel_id}')

    # Construct the full path to the settings.json file
    settings_file_path = os.path.join(target_directory, 'settings.json')

    # Check if the settings.json file exists
    if not os.path.exists(settings_file_path):
        raise FileNotFoundError(f"The settings.json file was not found in {settings_file_path}")

    # Read the settings.json file
    with open(settings_file_path, 'r') as file:
        settings_data = json.load(file)

    return settings_data


def write_settings_ini(panel_id, settings_dict):
    """
    Write parameters from a settings dictionary to a settings.ini file.
    
    :param panel_id: The panel ID to set specific parameters.
    :param settings_dict: The dictionary containing settings from the JSON file.
    """
    # Create a ConfigParser object
    config = configparser.ConfigParser()
    
    # Explicitly preserve case of keys by subclassing ConfigParser
    class MyConfigParser(configparser.ConfigParser):
        def optionxform(self, optionstr):
            return optionstr

    config = MyConfigParser()

    CHA_lna_number = settings_dict.get('daq-gain', 0)
    if CHA_lna_number not in [0, 1, 2]:
        CHA_lna_number = 0
    K, C = get_lna_params(CHA_lna_number)
    shc_enable = settings_dict.get('shc', False) 
    daq_triggering_threshold = settings_dict.get('daq-triggering-threshold', 800)
    # TrigL = int(1.08*(daq_triggering_threshold/1000 ) /(K *0.875) *8191 )
    TrigL = min(int(1.08 * (daq_triggering_threshold / 1000) / (K * 0.875) * 8191), 8000)
    print("Trigger Level:",TrigL)

    # Set default parameters
    config['Settings'] = {
        'CHA_Channel_select': int(panel_id)-1,  # panel_id corresponds to CH_A Channel_select
        'CHA_LNA_number': CHA_lna_number,  # Corresponds to daq-gain
        'CHB_Channel_select': 1,  # Default value
        'CHB_LNA_number': 1,  # Default value
        'NOP': settings_dict.get('min-no-of-pulses', 1000),  # Corresponds to min-no-of-pulses
        'PWL': settings_dict.get('samples-per-waveform', 256),  # Corresponds to samples-per-waveform
        'TrigL': TrigL,  
        'Trigpos': settings_dict.get('prpd-col', 64),  # Corresponds to max-daq-d,
        'Health_check_enable': shc_enable,  # Default value
        'Health_check_channel_select': int(panel_id) - 1,  # Default value
        'Max_duration': settings_dict.get('max-daq-d', 100)  # Corresponds to max-daq-d
    }

    # Define the path where the settings.ini file will be saved
    target_directory = os.path.join(main_path, 'DataTransfer', f'CH{panel_id}')
    ini_file_path = os.path.join(target_directory, 'settings.ini')

    # Write to the settings.ini file
    with open(ini_file_path, 'w') as configfile:
        config.write(configfile)

    print(f"Settings.ini has been written to {ini_file_path}")

def write_multi_trigger_settings_ini(panel_id, settings_dict, iteration):
    """
    Write parameters from a settings dictionary to a settings.ini file for alternate mode.
    :param panel_id: The panel ID to set specific parameters.
    :param settings_dict: The dictionary containing settings from the JSON file.
    :param iteration: The current iteration number (1, 2, 3, or 4).
    """
    # Create a ConfigParser object
    class MyConfigParser(configparser.ConfigParser):
        def optionxform(self, optionstr):
            return optionstr  # Preserve case sensitivity for options

    config = MyConfigParser()

    # Dynamically get gear and trigger values for the current iteration
    gear_key = f"gear_{iteration}"
    trigger_key = f"trigger_val_{iteration}"
    sample_count_key = f"sample_count_{iteration}"
    max_duration_key = f"sampling_time_{iteration}"
    shc_enable = settings_dict.get('shc', False) 
    CHA_LNA_number = settings_dict.get(gear_key, 0)  # Default to 0 if key is missing
    K, C = get_lna_params(CHA_LNA_number)
    TrigL = settings_dict.get(trigger_key, 800)  # Default to 800 if key is missing
    sample_time=settings_dict.get(max_duration_key, 800)
    # TrigL = int(1.08*(TrigL/1000 ) /(K *0.875) *8191 )
    TrigL = min(int(1.08 * (TrigL / 1000) / (K * 0.875) * 8191), 8000)
    NOP = settings_dict.get(sample_count_key, 1000)  # Default to 1000 if key is missing

    if CHA_LNA_number not in [0, 1, 2]:
        CHA_LNA_number = 0  # Validate CHA_LNA_number

    # Set parameters for the settings.ini file
    config['Settings'] = {
        'CHA_Channel_select': int(panel_id) - 1,  # panel_id corresponds to CH_A Channel_select
        'CHA_LNA_number': CHA_LNA_number,  # Use gear_<n> for alternate mode
        'CHB_Channel_select': 1,  # Default value
        'CHB_LNA_number': 1,  # Default value
        'NOP': NOP,  # Corresponds to min-no-of-pulses
        'PWL': settings_dict.get('samples-per-waveform', 256),  # Corresponds to samples-per-waveform
        'TrigL': TrigL,  # Use trigger_val_<n> for alternate mode
        'Trigpos': settings_dict.get('prpd-col', 64),  # Corresponds to max-daq-d,
        'Health_check_enable': shc_enable,  # Default value
        'Health_check_channel_select': int(panel_id)-1,  # Default value
        'Max_duration': sample_time  # Corresponds to max-daq-d
    }

    # Define the path where the settings.ini file will be saved
    target_directory = os.path.join(main_path, 'DataTransfer', f'CH{panel_id}')
    ini_file_path = os.path.join(target_directory, 'settings.ini')

    # Write to the settings.ini file
    with open(ini_file_path, 'w') as configfile:
        config.write(configfile)

    print(f"multi trigger settings.ini (iteration {iteration}) has been written to {ini_file_path}")


def run_downloadchannelsinfo():
    """
    Execute goblobarm32_1204 -downloadchannelsinfo command in the Channel_info directory.
    """
    # Construct the path to the Channel_info directory
    target_directory = os.path.join(main_path, 'DataTransfer', 'Channel_info')

    # Construct the path to the executable in the DataTransfer directory
    executable_path = os.path.join(main_path, 'DataTransfer', 'goblobarm32_1204')

    # Change to the target directory
    os.chdir(target_directory)

    # Execute the command to download channel info
    command = f'{executable_path} -downloadchannelsinfo'
    subprocess.run(command, shell=True)

    # Optionally, change back to the original directory
    os.chdir(main_path)

def run_channelsinfochanged():
    """
    Execute goblobarm32_1204 -channelsinfochanged command in the Channel_info directory
    and determine the return value.
    """
    # Construct the path to the Channel_info directory
    target_directory = os.path.join(main_path, 'DataTransfer', 'Channel_info')

    # Construct the path to the executable in the DataTransfer directory
    executable_path = os.path.join(main_path, 'DataTransfer', 'goblobarm32_1204')

    # Change to the target directory
    os.chdir(target_directory)

    # Execute the command and capture the return value
    command = f'{executable_path} -channelsinfochanged'
    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    # Print the output of the command
    output = result.stdout.strip()
    print("Command output:", output)

    # Determine and print the result
    if output == "true":
        return True
    elif output == "false":
        return False
    else:
        print("Result is Other:", output)
        return None
    # Optionally, change back to the original directory
    os.chdir(main_path)

def read_channelinfo_json():
    """
    Read the channelinfo JSON file from the Channel_info directory and return its content as a dictionary.

    :return: A dictionary containing the contents of the JSON file.
    """
    # Construct the path to the Channel_info directory
    channel_info_dir = os.path.join(main_path, 'DataTransfer', 'Channel_info')

    # Construct the full path to the channelinfo JSON file
    json_file_path = os.path.join(channel_info_dir, 'channelsinfo.json')

    # Check if the file exists
    if not os.path.exists(json_file_path):
        raise FileNotFoundError(f"The file {json_file_path} does not exist.")
    
    # Read the JSON file
    with open(json_file_path, 'r') as file:
        channelinfo_data = json.load(file)
    
    return channelinfo_data

def combine_rawdata(panel_id):
    """
    Combine rawdata1.txt, rawdata2.txt, rawdata3.txt, and rawdata4.txt into a single file rawdata_combo.txt.
    The first row of rawdata2.txt, rawdata3.txt, and rawdata4.txt will be removed before combining.
    :param panel_id: The panel ID used to locate the rawdata files.
    """
    # Define the file paths
    target_directory = os.path.join(main_path, 'DataTransfer', f'CH{panel_id}')
    rawdata_files = [
        os.path.join(target_directory, f'rawdata{i}.txt') for i in range(1, 5)
    ]
    combined_file = os.path.join(target_directory, 'rawdata_combo.txt')
    rawdata_txt = os.path.join(target_directory, 'rawdata.txt')
    # List to store combined lines
    combined_lines = []

    for idx, file_path in enumerate(rawdata_files):
        if not os.path.exists(file_path):
            print(f"Error: {file_path} does not exist.")
            return

        try:
            with open(file_path, 'r') as file:
                lines = file.readlines()

                # For rawdata2, rawdata3, and rawdata4, remove the first line
                if idx > 0:
                    lines = lines[1:]

                # Add the remaining lines to the combined list
                combined_lines.extend(lines)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return

    # Write the combined lines to the new file
    try:
        with open(combined_file, 'w') as file:
            file.writelines(combined_lines)
        print(f"Combined raw data saved to {combined_file}")
    except Exception as e:
        print(f"Error writing to {combined_file}: {e}")
        # Copy rawdata_combo.txt to rawdata.txt
    try:
        shutil.copy(combined_file, rawdata_txt)
        print(f"rawdata_combo.txt has been copied to {rawdata_txt}")
    except Exception as e:
        print(f"Error copying to {rawdata_txt}: {e}")


def process_raw_data(panel_id, K, C, rawdata_filename='rawdata.txt', converted_filename='converted_pddata.txt', 
                     waveform_filename='waveform.csv', prpd_filename='prpd.csv'):

    # Construct the path to the panel's data directory
    data_directory = os.path.join(main_path, 'DataTransfer', f'CH{panel_id}')
    
    # Construct the full paths to input and output files
    input_file = os.path.join(data_directory, rawdata_filename)
    converted_file = os.path.join(data_directory, converted_filename)
    output_waveform_file = os.path.join(data_directory, waveform_filename)
    output_prpd = os.path.join(data_directory, prpd_filename)

    # Call the functions from process_rawdata.py
    print(f"Processing raw data for panel {panel_id} in {data_directory}")
    conversion_result=process_rawdata.convert_file(input_file, converted_file)
    if conversion_result == 0:
        print(f"Converted file saved to {converted_file}")
    elif conversion_result == -1:
        print("Conversion skipped: First row contained only '-1'. No further processing.")
        return None, None    
    print(f"Converted file saved to {converted_file}")
    
    waveform_data = process_rawdata.process_file(converted_file, output_waveform_file, K, C)
    print(f"Waveform data converted successfully")
    
    prpd_data = process_rawdata.process_phase_period(converted_file, output_prpd, K, C)
    print(f"PRPD data converted successfully")
    return waveform_data, prpd_data

def update_meta(settings_dict,meta_file, waveform_data):

    # 计算 waveform_data 的行数
    num_waveforms = waveform_data.shape[0]  # 行数
    waveform_len = waveform_data.shape[1]
    trigger_thre=settings_dict.get("daq-triggering-threshold")
    if settings_dict.get("lna", False) is True:
        # Find the minimum of "trigger_val_1" to "trigger_val_4"
        trigger_values = [
            settings_dict.get(f"trigger_val_{i}", float('inf')) for i in range(1, 5)
        ]
        trig_val = min(trigger_values) / 1000
    else:
        trig_val = trigger_thre / 1000    
    # 读取 meta.json 文件
    if not os.path.exists(meta_file):
        print(f"Error: {meta_file} does not exist.")
        return

    with open(meta_file, 'r') as file:
        meta_data = json.load(file)

    # 更新 no-of-waveforms-collected 字段
    meta_data['no-of-waveforms-collected'] = num_waveforms
    meta_data['samples-per-waveform'] = waveform_len
    meta_data["daq-triggering-threshold"]=trig_val
    meta_data['substation-id'] = "TESTSTATION-5"
    meta_data['panel-id'] = settings_dict.get("panel-id")
    # 将更新后的数据保存回 meta.json 文件
    with open(meta_file, 'w') as file:
        json.dump(meta_data, file, indent=4)


def multi_trigger_mode(panel_id, settings_dict):
    # Initialize lists to store waveform and PRPD data for all iterations
    all_waveform_data = []
    all_prpd_data = []

    print(f"Entering multi trigger mode for panel {panel_id}...")
    for i in range(1, 5):  # Loop 4 times
        print(f"Multi trigger mode iteration {i} for panel {panel_id}...")
        
        # Write the settings to the settings.ini file
        write_multi_trigger_settings_ini(panel_id, settings_dict, i)
        print(f"Settings.ini file written for panel {panel_id} (Multi Trigger Mode, Iteration {i}).")

        # Copy settings.ini to the Program directory
        source_ini_file = os.path.join(main_path, 'DataTransfer', f'CH{panel_id}', 'settings.ini')
        destination_dir = os.path.join(main_path, 'Program')
        shutil.copy(source_ini_file, destination_dir)
        print(f"Settings.ini copied to {destination_dir} (Multi Trigger Mode, Iteration {i}).")

        # Change to the target directory and run the ELF file
        target_directory = os.path.join(main_path, 'DataTransfer', f'CH{panel_id}')
        os.chdir(target_directory)
        elf_file_path = os.path.join(main_path, 'Program', 'registor_set.elf')
        
        print(f"Running ELF file in multi trigger mode (Iteration {i})...")
        subprocess.run([elf_file_path], check=True)
        print(f"multi trigger mode ELF execution completed successfully (Iteration {i}).")

        # Rename rawdata.txt to rawdata{i}.txt
        rawdata_file = os.path.join(target_directory, 'rawdata.txt')
        renamed_rawdata_file = os.path.join(target_directory, f'rawdata{i}.txt')
        if os.path.exists(rawdata_file):
            shutil.copy(rawdata_file, renamed_rawdata_file)
            print(f"Raw data saved as {renamed_rawdata_file}.")
        else:
            print(f"Warning: {rawdata_file} does not exist. Skipping rename.")
        # combine_rawdata(panel_id)
    
    
    for i in range(1, 5):
        rawdata_file = os.path.join(target_directory, f'rawdata{i}.txt')
        converted_file = os.path.join(target_directory, f'converted_pddata{i}.txt')
        waveform_file = os.path.join(target_directory, f'waveform{i}.csv')
        prpd_file = os.path.join(target_directory, f'prpd{i}.csv')
        gear_key = f'gear_{i}'  
        lna_number = settings_dict.get(gear_key, 0)  
        K, C = get_lna_params(lna_number)
        print(f"Processing rawdata file {rawdata_file} (Iteration {i})...")
        waveform_data, prpd_data = process_raw_data(panel_id, K, C,
                                                    rawdata_filename=os.path.basename(rawdata_file),
                                                    converted_filename=os.path.basename(converted_file),
                                                    waveform_filename=os.path.basename(waveform_file),
                                                    prpd_filename=os.path.basename(prpd_file))
        # 只有当 waveform_data 和 prpd_data 都不是 None 时，才加入列表
        if waveform_data is not None and prpd_data is not None:
            print("None not in waveform prpd")
            all_waveform_data.append(waveform_data)
            all_prpd_data.append(prpd_data)
            print(f"rawdata{i}.txt has been processed successfully.")
        else:
            print(f"Skipping rawdata{i}.txt due to missing data.")
    # Combine all waveform and PRPD data
    # print(all_waveform_data)
    if all_waveform_data and all_prpd_data: 
        print("Combining PRPD AND WAVEFORM.")
        combined_waveform_data = pd.concat(all_waveform_data, axis=0, ignore_index=True)
        combined_prpd_data = pd.concat(all_prpd_data, axis=1, ignore_index=True)  # 按列拼接
        waveform_file = os.path.join(target_directory, 'waveform.csv')
        prpd_file = os.path.join(target_directory, 'prpd.csv')
        combined_waveform_data.to_csv(waveform_file, sep='\t',index=False, header=False)
        combined_prpd_data.to_csv(prpd_file, sep='\t',index=False, header=False)
        print("All waveform and PRPD data combined successfully.")
    else:
        print("No valid waveform or PRPD data found. Skipping merging process.")
        combined_waveform_data=None
        combined_prpd_data=None
    return combined_waveform_data, combined_prpd_data



def normal_mode(panel_id, settings_dict):
    """
    Perform operations specific to normal mode.
    :param panel_id: Panel ID.
    :param settings_dict: Dictionary of settings.
    """
    print(f"Entering normal mode for panel {panel_id}...")
    # Write the settings to the settings.ini file
    write_settings_ini(panel_id, settings_dict)
    print(f"Settings.ini file written for panel {panel_id} (Normal Mode).")

    source_ini_file = os.path.join(main_path, 'DataTransfer', f'CH{panel_id}', 'settings.ini')
    destination_dir = os.path.join(main_path, 'Program')       
    shutil.copy(source_ini_file, destination_dir)
    print(f"Settings.ini copied to {destination_dir} (Normal Mode).")

    target_directory = os.path.join(main_path, 'DataTransfer', f'CH{panel_id}')
    waveform_file = os.path.join(target_directory, 'waveform.csv')
    prpd_file = os.path.join(target_directory, 'prpd.csv')
    os.chdir(target_directory)
    elf_file_path = os.path.join(main_path, 'Program', 'registor_set.elf')
    
    print(f"Running ELF file in normal mode...")
    subprocess.run([elf_file_path], check=True)
    print(f"Normal mode ELF execution completed successfully.")

    lna_number = settings_dict.get('daq-gain', 0)
    K, C = get_lna_params(lna_number)
    waveform_data, prpd_data = process_raw_data(panel_id,K,C)
    # 只有当 waveform_data 和 prpd_data 都不是 None 时，才执行 .to_csv()
    if waveform_data is not None and prpd_data is not None:
        prpd_data.to_csv(prpd_file, sep='\t', index=False, header=False)
        waveform_data.to_csv(waveform_file, sep='\t', index=False, header=False)
        print("PRPD and waveform data successfully saved.")
    else:
        print("Skipping CSV saving because processing failed.")    
    # Return the processed data
    return waveform_data, prpd_data

def Cluster_and_save(waveform_data, prpd_data, K, output_dir):

    # 对 waveform 数据的 FFT 结果进行 KMeans 聚类
    labels = process_rawdata.waveform_cluster_fft(waveform_data, K)

    # 生成 AI cluster 字典
    ai_cluster_dict = process_rawdata.ai_cluster_gen(labels)

    # 保存 AI cluster 数据到 JSON 文件
    ai_cluster_json_path = f"{output_dir}/sensor-ai-cluster.json"
    process_rawdata.save_ai_cluster_to_json(ai_cluster_dict, ai_cluster_json_path)

    print(f"AI cluster data saved to {ai_cluster_json_path}")

    return ai_cluster_dict


def data_acquisition(channelinfo_dict):

    # Extract the panels list from the channelinfo_dict
    panels = channelinfo_dict.get('panels', [])
    # Loop through each panel in the list
    for panel_path in panels:
        # Extract panel ID from the panel path (assuming it's the last part of the path)
        panel_id_str = panel_path.split('/')[-1]  # "TESTPANEL-1"
        panel_id = panel_id_str.split('-')[-1]  # Extract the numeric part "1"
        print(f"\nStarting data acquisition for panel: {panel_id}")

        # Check if settings have changed
        settings_changed = run_settingschanged(panel_id)
        if settings_changed is True:
            print(f"Settings changed for {panel_id}, downloading settings...")
            run_downloadsettings(panel_id)
        elif settings_changed is False:
            print(f"No settings change detected for {panel_id}, skipping download.")
        else:
            print(f"Unexpected result for {panel_id}: {settings_changed}")
        
        # Perform the data acquisition here (additional data acquisition logic can be added)
        try:
            settings_dict = read_settings_json(panel_id)
            print(f"Read settings for panel {panel_id}")
            # 判断是否为 alternate 模式
            if settings_dict.get("alternate-mode", False) is True:
                print("Entering alternate mode...")

                # Step 1: Set gear values to 0
                for i in range(1, 5):
                    settings_dict[f"gear_{i}"] = 0
                print(f"Updated settings (gear values set to 0) for alternate mode...")
                
                # Perform multi-trigger mode with gear values set to 0
                waveform_data, prpd_data = multi_trigger_mode(panel_id, settings_dict)
                if waveform_data is None or prpd_data is None:
                    print(f"Skipping further processing for panel: {panel_id} due to missing data.")
                    send_mqtt_message(panel=panel_id, extra_msg="Missing Data")  
                else:               
                    # Perform clustering and saving for this configuration
                    cluster_num = settings_dict.get('no-of-cluster', 1) or 4
                    sensor_ai_cluster_path = os.path.join(main_path, 'DataTransfer', f'CH{panel_id}')
                    Cluster_and_save(waveform_data, prpd_data, cluster_num, sensor_ai_cluster_path)
                    meta_file = os.path.join(main_path, 'DataTransfer', f'CH{panel_id}', 'meta.json')
                    update_meta(settings_dict, meta_file, waveform_data)
                    run_uploaddata(panel_id)

                # Step 2: Set gear values to 2
                for i in range(1, 5):
                    settings_dict[f"gear_{i}"] = 2
                print(f"Updated settings (gear values set to 2) for alternate mode...")

                # Perform multi-trigger mode with gear values set to 2
                waveform_data, prpd_data = multi_trigger_mode(panel_id, settings_dict)
                if waveform_data is None or prpd_data is None:
                    print(f"Skipping further processing for panel: {panel_id} due to missing data.")
                    send_mqtt_message(panel=panel_id, extra_msg="Missing Data")  
                else:
                # Perform clustering and saving for this configuration
                    cluster_num = settings_dict.get('no-of-cluster', 1) or 4
                    Cluster_and_save(waveform_data, prpd_data, cluster_num, sensor_ai_cluster_path)
                    update_meta(settings_dict, meta_file, waveform_data)
                    run_uploaddata(panel_id)
                    send_mqtt_message(panel=panel_id, extra_msg="Data uploaded")  
            else:
                if settings_dict.get("lna", False) is True:
                    waveform_data, prpd_data = multi_trigger_mode(panel_id, settings_dict)
                else:       
                    waveform_data, prpd_data = normal_mode(panel_id, settings_dict)
                 # 如果任意一个是 None，跳过后续步骤
                if waveform_data is None or prpd_data is None:
                    print(f"Skipping further processing for panel: {panel_id} due to missing data.")
                    send_mqtt_message(panel=panel_id, extra_msg="Missing Data")  
                else:
                    # Perform the data acquisition here (additional data acquisition logic can be added)
                    print(f"Data acquisition completed for panel: {panel_id}")
                    cluster_num = settings_dict.get('no-of-cluster', 1) or 4
                    sensor_ai_cluster_path = os.path.join(main_path, 'DataTransfer', f'CH{panel_id}')
                    Cluster_and_save(waveform_data, prpd_data, cluster_num, sensor_ai_cluster_path)
                    meta_file =os.path.join(main_path, 'DataTransfer', f'CH{panel_id}','meta.json')
                    update_meta(settings_dict,meta_file, waveform_data)
                    run_uploaddata(panel_id)
                    send_mqtt_message(panel=panel_id, extra_msg="Data uploaded")  
        except FileNotFoundError as e:
            print(f"Error reading settings.json for panel {panel_id}: {e}")
        except Exception as e:
            print(f"An error occurred while processing panel {panel_id}: {e}")
        



# Example usage
if __name__ == "__main__":
    get_main_path()
    load_kernel_module()
    iteration_count = 0  # 初始化计数器
    while True:
        iteration_count += 1  # 每次循环增加计数
        print(f"\nStarting DAQ iteration {iteration_count}...")
        # Check if channelsinfo has changed
        if run_channelsinfochanged() is True:
            print("Channels info has changed, downloading channel info...")
            run_downloadchannelsinfo()
        else:
            print("No changes in channels info.")

        channelsinfo_dict = read_channelinfo_json()
        upload_interval = channelsinfo_dict.get("upload-interval", 0) 
        print(channelsinfo_dict)
        data_acquisition(channelsinfo_dict)
        if upload_interval > 0:
            print(f"Sleeping for {upload_interval} seconds before the next acquisition...")
            time.sleep(upload_interval)
        else:
            print("Upload interval is set to 0, exiting loop.")


    

