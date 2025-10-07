import json
import os

# Define the base directory
base_dir = "/home/xilinx/PD_monitoring/DataTransfer"
channel_info_dir = os.path.join(base_dir, "Channel_info")  # Channel_info directory

# New substation ID to be updated
new_substation_id = "TESTSTATION-2"

# Process CH1 to CH9 directories
for ch in range(1, 10):
    ch_dir = os.path.join(base_dir, f"CH{ch}")
    
    for file_name in ["meta.json", "settings.json"]:
        file_path = os.path.join(ch_dir, file_name)
        
        if os.path.exists(file_path):
            # Read the JSON file
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Update "substation-id" if it exists
            if "substation-id" in data:
                data["substation-id"] = new_substation_id
                
                # Write back the updated JSON file
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)

                print(f"Updated {file_path} -> substation-id: {new_substation_id}")

# Process Channel_info directory
for file_name in ["channelsinfo.json", "settings.json"]:
    file_path = os.path.join(channel_info_dir, file_name)
    
    if os.path.exists(file_path):
        # Read the JSON file
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Update "substation-id" if it exists
        if "substation-id" in data:
            data["substation-id"] = new_substation_id
            
            # Write back the updated JSON file
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

            print(f"Updated {file_path} -> substation-id: {new_substation_id}")

print("All files updated successfully!")
