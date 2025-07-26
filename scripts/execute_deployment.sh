#!/usr/bin/expect -f

# AUREN Automated Deployment Execution
# This script will handle all password prompts automatically

set timeout -1
set password ".HvddX+@6dArsKd"

# Start the master deployment script
spawn ./scripts/master_deploy.sh

# Handle all prompts
expect {
    "*password:*" {
        send "$password\r"
        exp_continue
    }
    "*(yes/no)*" {
        send "yes\r"
        exp_continue
    }
    "*fingerprint*" {
        send "yes\r"
        exp_continue
    }
    eof
}

puts "\n✅ Deployment completed!" 