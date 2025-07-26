-- AUREN PHI Encryption at Rest Functions
-- HIPAA-compliant AES-256 encryption for protected health information

-- Enable pgcrypto extension for encryption functions
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Create encryption key table (keys should be stored securely, this is for demo)
CREATE TABLE IF NOT EXISTS encryption_keys (
    id SERIAL PRIMARY KEY,
    key_name VARCHAR(50) UNIQUE NOT NULL,
    key_value TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    active BOOLEAN DEFAULT true
);

-- Insert default encryption key (in production, use key management service)
INSERT INTO encryption_keys (key_name, key_value)
VALUES ('phi_master_key', encode(gen_random_bytes(32), 'base64'))
ON CONFLICT (key_name) DO NOTHING;

-- Function to encrypt PHI data
CREATE OR REPLACE FUNCTION encrypt_phi(data TEXT)
RETURNS TEXT AS $$
DECLARE
    encryption_key BYTEA;
BEGIN
    -- Get active encryption key
    SELECT decode(key_value, 'base64') INTO encryption_key
    FROM encryption_keys
    WHERE key_name = 'phi_master_key' AND active = true
    LIMIT 1;
    
    IF encryption_key IS NULL THEN
        RAISE EXCEPTION 'No active encryption key found';
    END IF;
    
    -- Encrypt data using AES-256
    RETURN encode(
        pgp_sym_encrypt(data, encode(encryption_key, 'hex'), 'cipher-algo=aes256'),
        'base64'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to decrypt PHI data
CREATE OR REPLACE FUNCTION decrypt_phi(encrypted_data TEXT)
RETURNS TEXT AS $$
DECLARE
    encryption_key BYTEA;
    decrypted_text TEXT;
BEGIN
    -- Get active encryption key
    SELECT decode(key_value, 'base64') INTO encryption_key
    FROM encryption_keys
    WHERE key_name = 'phi_master_key' AND active = true
    LIMIT 1;
    
    IF encryption_key IS NULL THEN
        RAISE EXCEPTION 'No active encryption key found';
    END IF;
    
    -- Decrypt data
    BEGIN
        decrypted_text := pgp_sym_decrypt(
            decode(encrypted_data, 'base64'),
            encode(encryption_key, 'hex')
        );
        RETURN decrypted_text;
    EXCEPTION
        WHEN OTHERS THEN
            -- Log decryption failure for audit
            RAISE WARNING 'PHI decryption failed: %', SQLERRM;
            RETURN NULL;
    END;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create audit table for PHI access
CREATE TABLE IF NOT EXISTS phi_access_audit (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255),
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    action VARCHAR(50),
    table_name VARCHAR(100),
    record_id VARCHAR(100),
    ip_address INET,
    success BOOLEAN DEFAULT true,
    error_message TEXT
);

-- Function to audit PHI access
CREATE OR REPLACE FUNCTION audit_phi_access(
    p_user_id VARCHAR(255),
    p_action VARCHAR(50),
    p_table_name VARCHAR(100),
    p_record_id VARCHAR(100),
    p_ip_address INET DEFAULT NULL,
    p_success BOOLEAN DEFAULT true,
    p_error_message TEXT DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO phi_access_audit (
        user_id, action, table_name, record_id, 
        ip_address, success, error_message
    ) VALUES (
        p_user_id, p_action, p_table_name, p_record_id,
        p_ip_address, p_success, p_error_message
    );
END;
$$ LANGUAGE plpgsql;

-- Create encrypted biometric data table
CREATE TABLE IF NOT EXISTS encrypted_biometric_data (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    metric_type VARCHAR(100) NOT NULL,
    encrypted_value TEXT NOT NULL,
    encrypted_metadata TEXT,
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, metric_type, timestamp)
);

-- Create index for time-series queries
CREATE INDEX idx_encrypted_biometric_time ON encrypted_biometric_data(user_id, timestamp DESC);

-- Function to store encrypted biometric data
CREATE OR REPLACE FUNCTION store_encrypted_biometric(
    p_user_id VARCHAR(255),
    p_metric_type VARCHAR(100),
    p_value TEXT,
    p_metadata JSONB,
    p_timestamp TIMESTAMP,
    p_accessor_id VARCHAR(255),
    p_ip_address INET DEFAULT NULL
)
RETURNS BOOLEAN AS $$
DECLARE
    encrypted_val TEXT;
    encrypted_meta TEXT;
BEGIN
    -- Encrypt the value and metadata
    encrypted_val := encrypt_phi(p_value);
    IF p_metadata IS NOT NULL THEN
        encrypted_meta := encrypt_phi(p_metadata::TEXT);
    END IF;
    
    -- Store encrypted data
    INSERT INTO encrypted_biometric_data (
        user_id, metric_type, encrypted_value, 
        encrypted_metadata, timestamp
    ) VALUES (
        p_user_id, p_metric_type, encrypted_val,
        encrypted_meta, p_timestamp
    ) ON CONFLICT (user_id, metric_type, timestamp) 
    DO UPDATE SET 
        encrypted_value = EXCLUDED.encrypted_value,
        encrypted_metadata = EXCLUDED.encrypted_metadata;
    
    -- Audit the access
    PERFORM audit_phi_access(
        p_accessor_id, 'STORE', 'encrypted_biometric_data',
        p_user_id || ':' || p_metric_type, p_ip_address
    );
    
    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        -- Audit the failure
        PERFORM audit_phi_access(
            p_accessor_id, 'STORE_FAILED', 'encrypted_biometric_data',
            p_user_id || ':' || p_metric_type, p_ip_address, 
            false, SQLERRM
        );
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

-- Grant necessary permissions
GRANT EXECUTE ON FUNCTION encrypt_phi(TEXT) TO auren_user;
GRANT EXECUTE ON FUNCTION decrypt_phi(TEXT) TO auren_user;
GRANT EXECUTE ON FUNCTION audit_phi_access(VARCHAR, VARCHAR, VARCHAR, VARCHAR, INET, BOOLEAN, TEXT) TO auren_user;
GRANT EXECUTE ON FUNCTION store_encrypted_biometric(VARCHAR, VARCHAR, TEXT, JSONB, TIMESTAMP, VARCHAR, INET) TO auren_user;
GRANT SELECT, INSERT ON encrypted_biometric_data TO auren_user;
GRANT SELECT, INSERT ON phi_access_audit TO auren_user;
GRANT USAGE ON SEQUENCE encrypted_biometric_data_id_seq TO auren_user;
GRANT USAGE ON SEQUENCE phi_access_audit_id_seq TO auren_user;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'PHI encryption at rest functions created successfully';
    RAISE NOTICE 'AES-256 encryption enabled for biometric data';
    RAISE NOTICE 'HIPAA-compliant audit logging activated';
END $$; 