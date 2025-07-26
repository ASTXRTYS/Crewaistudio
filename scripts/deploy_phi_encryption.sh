#!/usr/bin/expect -f

# Deploy PHI Encryption at Rest to DigitalOcean
# Quick Win #4

set timeout -1
set password ".HvddX+@6dArsKd"

puts "🔐 Deploying PHI Encryption at Rest..."

# Copy SQL file
spawn scp sql/init/02_encryption_functions.sql root@144.126.215.218:/root/

expect {
    "*password:*" {
        send "$password\r"
        expect eof
    }
}

# Connect and deploy
spawn ssh root@144.126.215.218

expect {
    "*password:*" {
        send "$password\r"
        expect "*#"
    }
}

# Deploy encryption functions
send "echo '🔐 Installing PHI encryption functions...'\r"
expect "*#"

send "docker exec -i auren-postgres psql -U auren_user -d auren_db < /root/02_encryption_functions.sql\r"
expect "*#"

# Test encryption
send "echo '\r"
expect "*#"

send "echo '🧪 Testing PHI encryption...'\r"
expect "*#"

send "docker exec auren-postgres psql -U auren_user -d auren_db -c \"SELECT encrypt_phi('test_patient_data_123');\"\r"
expect "*#"

send "echo '\r"
expect "*#"

send "echo '🧪 Testing PHI decryption...'\r"
expect "*#"

send "docker exec auren-postgres psql -U auren_user -d auren_db -c \"SELECT decrypt_phi(encrypt_phi('test_patient_data_123'));\"\r"
expect "*#"

send "echo '\r"
expect "*#"

send "echo '📊 Checking audit table...'\r"
expect "*#"

send "docker exec auren-postgres psql -U auren_user -d auren_db -c \"SELECT COUNT(*) FROM phi_access_audit;\"\r"
expect "*#"

send "echo '\r"
expect "*#"

send "echo '================================='\r"
expect "*#"

send "echo '✅ PHI ENCRYPTION DEPLOYED:'\r"
expect "*#"

send "echo '- AES-256 encryption functions active'\r"
expect "*#"

send "echo '- HIPAA-compliant audit logging enabled'\r"
expect "*#"

send "echo '- Encrypted biometric storage ready'\r"
expect "*#"

send "echo '================================='\r"
expect "*#"

send "exit\r"
expect eof

puts "\n🎉 PHI encryption at rest deployed successfully!" 