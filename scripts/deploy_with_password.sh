#!/usr/bin/expect -f

# AUREN Automated Deployment with Password
# WARNING: This script contains your password - keep it secure!

set timeout -1
set password "YOUR_PASSWORD_HERE"

spawn ./scripts/master_deploy.sh

# Handle all password prompts
expect {
    "*password:*" {
        send "$password\r"
        exp_continue
    }
    "*(yes/no)*" {
        send "yes\r"
        exp_continue
    }
    eof
}

puts "\n✅ Deployment completed!" 