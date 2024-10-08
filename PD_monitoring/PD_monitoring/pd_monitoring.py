import os
import subprocess
import json
import configparser
import time
import shutil
main_path = None

def get_main_path():
    """ 
    Get the current working directory path at the time of program execution
    and assign it to the global variable main_path.
    :return: The absolute path of the current working directory.
    """
    global main_path
    main_path = os.getcwd()

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
        return None
        print("ERROR! error message:", output)

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
    CHA_lna_number = settings_dict.get('daq-gain', 1)
    if CHA_lna_number not in [0, 1, 2]:
        CHA_lna_number = 0
    # Set default parameters
    config['Settings'] = {
        'CHA_Channel_select': int(panel_id)-1,  # panel_id corresponds to CH_A Channel_select
        'CHA_LNA_number': CHA_lna_number,  # Corresponds to daq-gain
        'CHB_Channel_select': 1,  # Default value
        'CHB_LNA_number': 1,  # Default value
        'NOP': settings_dict.get('min-no-of-pulses', 1000),  # Corresponds to min-no-of-pulses
        'PWL': settings_dict.get('samples-per-waveform', 256),  # Corresponds to samples-per-waveform
        'TrigL': settings_dict.get('daq-triggering-threshold', 800),  # Corresponds to daq-triggering-threshold
        'Health_check_enable': False,  # Default value
        'Health_check_channel_select': 1,  # Default value
        'Max_duration': settings_dict.get('max-daq-d', 100)  # Corresponds to max-daq-d
    }

    # Define the path where the settings.ini file will be saved
    target_directory = os.path.join(main_path, 'DataTransfer', f'CH{panel_id}')
    ini_file_path = os.path.join(target_directory, 'settings.ini')

    # Write to the settings.ini file
    with open(ini_file_path, 'w') as configfile:
        config.write(configfile)

    print(f"Settings.ini has been written to {ini_file_path}")

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

def data_acquisition(channelinfo_dict):
    """
    Perform data acquisition for each panel in the channelinfo_dict.
    
    :param channelinfo_dict: A dictionary containing channel information, including a list of panels.
    """
    ko_file_path = os.path.join(main_path, 'Program', 'adc-axi-dma.ko')
    try:
        print(f"Loading kernel module {ko_file_path}...")
        subprocess.run(['insmod', ko_file_path], check=True)
        print(f"Kernel module {ko_file_path} loaded successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to load kernel module {ko_file_path}: {e}")
        print("Continuing without exiting...")
    # Extract the panels list from the channelinfo_dict
    panels = channelinfo_dict.get('panels', [])
    # Loop through each panel in the list
    for panel_path in panels:
        # Extract panel ID from the panel path (assuming it's the last part of the path)
        panel_id_str = panel_path.split('/')[-1]  # "TESTPANEL-1"
        panel_id = panel_id_str.split('-')[-1]  # Extract the numeric part "1"
        print(f"\nStarting data acquisition for panel: {panel_id}")

        # Check if settings have changed
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
            
            # Write the settings to the settings.ini file
            write_settings_ini(panel_id, settings_dict)
            print(f"Settings.ini file written for panel {panel_id}")

            source_ini_file = os.path.join(main_path, 'DataTransfer', f'CH{panel_id}', 'settings.ini')
            destination_dir = os.path.join(main_path, 'Program')       
            shutil.copy(source_ini_file, destination_dir)
            print(f"Settings.ini copied to {destination_dir}")

            target_directory = os.path.join(main_path, 'DataTransfer', f'CH{panel_id}')
            os.chdir(target_directory)
            elf_file_path = os.path.join(main_path, 'Program', 'registor_set.elf')
            
            current_dir = os.getcwd()
            print(f"Current working directory before running ELF: {current_dir}")           
            # Execute the ELF file
            subprocess.run([elf_file_path], check=True)
            print(f"Executed {elf_file_path} successfully.")
            

        except FileNotFoundError as e:
            print(f"Error reading settings.json for panel {panel_id}: {e}")
        except Exception as e:
            print(f"An error occurred while processing panel {panel_id}: {e}")
        
        # Perform the data acquisition here (additional data acquisition logic can be added)
        print(f"Data acquisition completed for panel: {panel_id}")
        time.sleep(3)

# Example usage
if __name__ == "__main__":
    get_main_path()

    # Check if channelsinfo has changed
    if run_channelsinfochanged() is True:
        print("Channels info has changed, downloading channel info...")
        run_downloadchannelsinfo()
    else:
        print("No changes in channels info.")

    channelsinfo_dict = read_channelinfo_json()
    # print(channelsinfo_dict)
    data_acquisition(channelsinfo_dict)

    

