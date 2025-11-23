# Snowflake Authentication Guide

SOGS supports three authentication methods to connect to your Snowflake account:

1. **Password Authentication** (simplest)
2. **Private Key Authentication** (more secure)
3. **Configuration File** (best for managing multiple connections)

## 1. Password Authentication

This is the simplest method, ideal for getting started quickly.

### Usage

**Via Web UI:**
1. Navigate to `http://localhost:8000`
2. Select "Password Authentication" tab
3. Fill in your credentials:
   - Account: Your Snowflake account identifier
   - User: Your Snowflake username
   - Password: Your Snowflake password
   - Optional: Warehouse, Database, Schema, Role
4. Click "Connect to Snowflake"

**Via API:**
```bash
curl -X POST "http://localhost:8000/api/credentials/configure" \
  -H "Content-Type: application/json" \
  -d '{
    "account": "abc12345",
    "user": "your_username",
    "password": "your_password",
    "warehouse": "COMPUTE_WH",
    "database": "YOUR_DATABASE",
    "schema": "PUBLIC",
    "role": "ACCOUNTADMIN"
  }'
```

---

## 2. Private Key Authentication

More secure than password authentication, recommended for production environments.

### Step 1: Generate RSA Key Pair

```bash
# Generate private key (with passphrase)
openssl genrsa 2048 | openssl pkcs8 -topk8 -v2 des3 -inform PEM -out rsa_key.p8

# Or generate without passphrase
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8 -nocrypt

# Generate public key
openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub
```

### Step 2: Add Public Key to Snowflake User

```sql
-- Get the public key content (remove header/footer)
-- Copy the content between -----BEGIN PUBLIC KEY----- and -----END PUBLIC KEY-----

-- Add to Snowflake user
ALTER USER your_username SET RSA_PUBLIC_KEY='MIIBIjANBgkqhki...';

-- Verify
DESC USER your_username;
```

### Step 3: Configure SOGS with Private Key

**Via Web UI:**
1. Navigate to `http://localhost:8000`
2. Select "Private Key Authentication" tab
3. Fill in:
   - Account: Your Snowflake account identifier
   - User: Your Snowflake username
   - Private Key Path: Full path to your `.p8` file (e.g., `/home/user/.ssh/rsa_key.p8`)
   - Private Key Passphrase: If you used a passphrase (optional)
   - Optional: Warehouse, Database, Schema, Role
4. Click "Connect with Private Key"

**Via API:**
```bash
curl -X POST "http://localhost:8000/api/credentials/configure-with-key" \
  -H "Content-Type: application/json" \
  -d '{
    "account": "abc12345",
    "user": "your_username",
    "private_key_path": "/path/to/rsa_key.p8",
    "private_key_passphrase": "optional_passphrase",
    "warehouse": "COMPUTE_WH",
    "database": "YOUR_DATABASE",
    "schema": "PUBLIC",
    "role": "ACCOUNTADMIN"
  }'
```

### Security Best Practices

1. **Protect your private key:**
   ```bash
   chmod 600 /path/to/rsa_key.p8
   ```

2. **Use a passphrase** for additional security

3. **Never commit private keys** to version control

4. **Rotate keys regularly** (recommended every 90 days)

5. **Store keys securely** (use secret management tools in production)

---

## 3. Configuration File Authentication

Best for managing multiple Snowflake connections (dev, staging, production).

### Supported Formats

- **JSON** (`.json`)
- **TOML** (`.toml`)

### Step 1: Create Configuration File

**JSON Format (`snowflake_config.json`):**
```json
{
  "default": {
    "account": "abc12345",
    "user": "your_username",
    "password": "your_password",
    "warehouse": "COMPUTE_WH",
    "database": "YOUR_DATABASE",
    "schema": "PUBLIC",
    "role": "ACCOUNTADMIN"
  },
  "production": {
    "account": "orgname-accountname",
    "user": "prod_user",
    "private_key_path": "/path/to/rsa_key.p8",
    "private_key_passphrase": "optional_passphrase",
    "warehouse": "PROD_WH",
    "database": "PRODUCTION_DB",
    "schema": "PUBLIC",
    "role": "SYSADMIN"
  }
}
```

**TOML Format (`snowflake_config.toml`):**
```toml
[default]
account = "abc12345"
user = "your_username"
password = "your_password"
warehouse = "COMPUTE_WH"
database = "YOUR_DATABASE"
schema = "PUBLIC"
role = "ACCOUNTADMIN"

[production]
account = "orgname-accountname"
user = "prod_user"
private_key_path = "/path/to/rsa_key.p8"
private_key_passphrase = "optional_passphrase"
warehouse = "PROD_WH"
database = "PRODUCTION_DB"
schema = "PUBLIC"
role = "SYSADMIN"
```

See `examples/` directory for complete examples.

### Step 2: Configure SOGS

**Via Web UI:**
1. Navigate to `http://localhost:8000`
2. Select "Configuration File" tab
3. Fill in:
   - Config File Path: Full path to your config file (e.g., `/path/to/snowflake_config.json`)
   - Connection Name: Name of the connection profile (e.g., `production`, `default`)
4. Click "Connect from Config File"

**Via API:**
```bash
curl -X POST "http://localhost:8000/api/credentials/configure-from-file" \
  -H "Content-Type: application/json" \
  -d '{
    "config_path": "/path/to/snowflake_config.json",
    "connection_name": "production"
  }'
```

### Configuration File Security

1. **Protect your config file:**
   ```bash
   chmod 600 /path/to/snowflake_config.json
   ```

2. **Never commit credentials** to version control
   - Add to `.gitignore`: `*.config.json`, `*.config.toml`

3. **Use environment-specific files:**
   - `snowflake.dev.json`
   - `snowflake.prod.json`

4. **Consider using private keys** instead of passwords in config files

---

## Docker Deployment with Authentication

### Using Environment Variables

```yaml
# docker-compose.yml
version: '3.8'
services:
  sogs:
    build: .
    ports:
      - "8000:8000"
    volumes:
      # Mount private key
      - ./rsa_key.p8:/app/rsa_key.p8:ro
      # Mount config file
      - ./snowflake_config.json:/app/snowflake_config.json:ro
    environment:
      - SNOWFLAKE_ACCOUNT=abc12345
      - SNOWFLAKE_USER=your_username
      # For password auth
      - SNOWFLAKE_PASSWORD=your_password
```

### Using Config File in Docker

```bash
# Run with mounted config file
docker run -p 8000:8000 \
  -v $(pwd)/snowflake_config.json:/app/snowflake_config.json:ro \
  sogs:latest
```

### Using Private Key in Docker

```bash
# Run with mounted private key
docker run -p 8000:8000 \
  -v $(pwd)/rsa_key.p8:/app/rsa_key.p8:ro \
  sogs:latest
```

---

## Account Identifier Formats

SOGS automatically normalizes account identifiers. You can use any of these formats:

| Format | Example | Description |
|--------|---------|-------------|
| Account Locator | `abc12345` | Legacy format |
| Locator with Region | `abc12345.us-east-1` | With cloud region |
| Org-Account | `orgname-accountname` | Preferred format |
| Full URL | `abc12345.snowflakecomputing.com` | Auto-normalized |
| HTTPS URL | `https://abc12345.snowflakecomputing.com` | Auto-normalized |

---

## Troubleshooting Authentication

### Private Key Authentication Issues

**Error: "Failed to load private key"**
- Verify the file path is correct and accessible
- Check file permissions: `chmod 600 rsa_key.p8`
- Ensure the key is in PKCS#8 format (`.p8`)
- Verify passphrase if the key is encrypted

**Error: "JWT token is invalid"**
- Public key not added to Snowflake user
- Run: `ALTER USER your_username SET RSA_PUBLIC_KEY='...'`
- Verify: `DESC USER your_username;`

**Error: "Public and private key pair mismatch"**
- Regenerate the public key from your private key:
  ```bash
  openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub
  ```

### Config File Authentication Issues

**Error: "Config file not found"**
- Verify the file path is absolute (not relative)
- Check file exists: `ls -la /path/to/snowflake_config.json`
- Ensure file is accessible from Docker container (if using Docker)

**Error: "Failed to load config file"**
- Verify JSON/TOML syntax is valid
- Check for missing required fields (`account`, `user`)
- Ensure authentication method is specified (`password` or `private_key_path`)

**Error: "Connection name not found"**
- Verify connection name exists in config file
- Default connection name is `"default"`

---

## Security Recommendations

### For Development
- ✅ Password authentication is acceptable
- ✅ Store credentials in local config file
- ⚠️ Never commit credentials to git

### For Production
- ✅ **Use private key authentication**
- ✅ Use encrypted private keys with passphrases
- ✅ Store keys in secret management systems (AWS Secrets Manager, HashiCorp Vault, etc.)
- ✅ Rotate keys every 90 days
- ✅ Use least-privilege roles
- ✅ Enable multi-factor authentication (MFA) on Snowflake accounts
- ❌ Avoid password authentication
- ❌ Never store credentials in code or Docker images

### File Permissions

```bash
# Private key
chmod 600 /path/to/rsa_key.p8

# Config file
chmod 600 /path/to/snowflake_config.json

# Ensure owned by application user
chown app_user:app_group /path/to/rsa_key.p8
```

---

## API Reference

### POST `/api/credentials/configure`
Configure with password or private key (inline)

**Request Body:**
```json
{
  "account": "string",
  "user": "string",
  "password": "string (optional)",
  "private_key_path": "string (optional)",
  "private_key_passphrase": "string (optional)",
  "warehouse": "string (optional)",
  "database": "string (optional)",
  "schema": "string (optional)",
  "role": "string (optional)"
}
```

### POST `/api/credentials/configure-with-key`
Configure with private key authentication

**Request Body:**
```json
{
  "account": "string",
  "user": "string",
  "private_key_path": "string",
  "private_key_passphrase": "string (optional)",
  "warehouse": "string (optional)",
  "database": "string (optional)",
  "schema": "string (optional)",
  "role": "string (optional)"
}
```

### POST `/api/credentials/configure-from-file`
Configure from configuration file

**Request Body:**
```json
{
  "config_path": "string",
  "connection_name": "string (default: 'default')"
}
```

### GET `/api/credentials/test`
Test current credentials

**Response:**
```json
{
  "success": true,
  "message": "Connection successful",
  "version": "X.XX.X",
  "account": "ABC12345",
  "user": "USERNAME",
  "auth_method": "private_key"
}
```

---

## Examples

See the `examples/` directory for:
- `snowflake_config.json` - JSON configuration example
- `snowflake_config.toml` - TOML configuration example

---

## Additional Resources

- [Snowflake Key Pair Authentication](https://docs.snowflake.com/en/user-guide/key-pair-auth.html)
- [Snowflake Account Identifiers](https://docs.snowflake.com/en/user-guide/admin-account-identifier.html)
- [OpenSSL Key Generation](https://www.openssl.org/docs/man1.1.1/man1/genrsa.html)

---

**Need Help?** Check `TROUBLESHOOTING.md` for common connection issues.
