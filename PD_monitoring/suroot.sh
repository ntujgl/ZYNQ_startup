#!/usr/bin/expect -f

# Set the timeout to unlimited
set timeout -1

# Set the root password (replace with your actual password)
set root_password "xilinx"

# Start the su command to switch to root user
spawn su

# Wait for the "Password:" prompt and send the password
expect "Password:"
send "$root_password\r"

expect "#"
send "python3 /home/xilinx/PD_monitoring/pd_monitoring.py\r"

# After switching to root, keep the shell interactive for user input
interact
