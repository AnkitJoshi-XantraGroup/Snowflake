# Snowflake Connection Troubleshooting Guide

## Error 250001: Could not connect to Snowflake backend

This error typically occurs due to account identifier format issues or network connectivity problems.

## Fixed Issues

The application now includes:
1. **Automatic account identifier normalization** - handles various formats automatically
2. **Increased connection timeouts** - 60 seconds instead of default
3. **Better error messages** - specific guidance for common issues
4. **UI improvements** - clear examples of valid account formats

## Valid Account Identifier Formats

You can now enter your Snowflake account in any of these formats:

### Format 1: Account Locator (Legacy)
```
abc12345
```

### Format 2: Account Locator with Region
```
abc12345.us-east-1
abc12345.eu-west-1
```

### Format 3: Organization-Account Name (Preferred)
```
orgname-accountname
mycompany-production
```

### Format 4: Full URL (Auto-normalized)
```
abc12345.snowflakecomputing.com
https://abc12345.snowflakecomputing.com
```

**Note:** The application will automatically strip `.snowflakecomputing.com`, `https://`, and other common additions.

## How to Find Your Account Identifier

### Method 1: From Snowflake URL
When you log into Snowflake, look at the URL in your browser:
- URL: `https://abc12345.snowflakecomputing.com/...`
- Account ID: `abc12345`

Or for newer accounts:
- URL: `https://orgname-accountname.snowflakecomputing.com/...`
- Account ID: `orgname-accountname`

### Method 2: From Snowflake UI
1. Log into Snowflake
2. Click on your user profile (bottom left)
3. Hover over your account name
4. The account identifier will be shown

### Method 3: From ACCOUNT_LOCATOR
If you have access to Snowflake, run:
```sql
SELECT CURRENT_ACCOUNT();
SELECT CURRENT_ORGANIZATION_NAME() || '-' || CURRENT_ACCOUNT_NAME() as FULL_ACCOUNT_ID;
```

## Common Connection Issues and Solutions

### Issue 1: "Could not connect to Snowflake backend"

**Possible Causes:**
1. Incorrect account identifier format
2. Network/firewall blocking the connection
3. VPN required but not connected
4. Proxy configuration needed

**Solutions:**
- ✅ **Try different account formats** - The app now handles this automatically
- Check if you need to be on a VPN to access Snowflake
- Verify your network allows HTTPS traffic to `*.snowflakecomputing.com`
- Check for corporate firewalls or proxy settings

### Issue 2: "Incorrect username or password"

**Solutions:**
- Verify credentials in Snowflake web UI first
- Check for extra spaces in username/password
- Ensure Caps Lock is off
- Try resetting your Snowflake password

### Issue 3: "Account does not exist"

**Solutions:**
- Double-check the account identifier format
- Verify you're using the correct region
- Confirm account is active (not suspended/closed)

### Issue 4: Network timeout

**Solutions:**
- The app now uses 60-second timeouts (up from default)
- Check your internet connection
- Try from a different network
- Verify no firewall is blocking outbound HTTPS

## Testing Your Connection

### Step 1: Verify Credentials in Snowflake Web UI
Before using SOGS, ensure you can log in at:
```
https://YOUR_ACCOUNT.snowflakecomputing.com
```

### Step 2: Required Permissions
Your Snowflake user needs these privileges:
```sql
-- Minimum required grants
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE YOUR_ROLE;
GRANT USAGE ON WAREHOUSE YOUR_WAREHOUSE TO ROLE YOUR_ROLE;
```

For full SOGS functionality, use one of these roles:
- `ACCOUNTADMIN` (recommended for full features)
- `SYSADMIN` (most features)
- Custom role with appropriate grants

### Step 3: Test with SOGS
1. Restart your Python application or Docker container:
   ```bash
   # If running locally
   python app.py

   # If using Docker
   docker-compose restart
   ```

2. Navigate to `http://localhost:8000`

3. Enter credentials using any of the supported formats

4. Click "Connect to Snowflake"

## Network Requirements

SOGS needs to connect to:
- `*.snowflakecomputing.com` (port 443)
- OCSP endpoints for certificate validation

### Firewall Rules
Allow outbound HTTPS (port 443) to:
```
*.snowflakecomputing.com
ocsp.snowflakecomputing.com
```

### Proxy Configuration
If behind a corporate proxy, set environment variables:
```bash
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080
```

## Advanced Troubleshooting

### Enable Debug Logging

1. Edit `config.py`:
   ```python
   DEBUG = True
   ```

2. Set logging level in `app.py`:
   ```python
   logging.basicConfig(level=logging.DEBUG)
   ```

3. Check logs for detailed connection attempts

### Test Connection with Python Script

Create a test script `test_connection.py`:
```python
import snowflake.connector

conn = snowflake.connector.connect(
    account='YOUR_ACCOUNT',
    user='YOUR_USER',
    password='YOUR_PASSWORD',
    login_timeout=60,
    network_timeout=60
)

cursor = conn.cursor()
cursor.execute("SELECT CURRENT_VERSION()")
print("Snowflake version:", cursor.fetchone()[0])
cursor.close()
conn.close()
print("✅ Connection successful!")
```

Run it:
```bash
python test_connection.py
```

### Check Snowflake Connector Version
```bash
pip list | grep snowflake-connector
```

Should show: `snowflake-connector-python 3.6.0` or higher

## Still Having Issues?

### Check Application Logs
```bash
# If running locally
# Logs appear in console

# If using Docker
docker-compose logs -f sogs
```

### Verify Python Version
```bash
python --version
```
Should be Python 3.11 or higher

### Reinstall Dependencies
```bash
pip install --upgrade --force-reinstall snowflake-connector-python
```

## Example: Successful Connection

When connection is successful, you should see:
```
Connection successful (Snowflake version: X.XX.X)
```

The application will then allow you to:
- View cost summaries
- Analyze query performance
- Run governance checks
- Use migration tools

## Contact Information for Account Issues

If you believe your account identifier is correct but still cannot connect:
1. Contact your Snowflake administrator
2. Open a ticket with Snowflake Support
3. Check Snowflake status page: https://status.snowflake.com

## Updated Features (Latest Commit)

✅ Automatic account identifier normalization
✅ Increased connection timeouts (60 seconds)
✅ Detailed error messages with troubleshooting steps
✅ UI guidance showing valid account formats
✅ Better error display with formatted messages
✅ Connection info display (version, account, user)

## Need More Help?

Check the main README.md for:
- Installation instructions
- Feature documentation
- API reference
- Deployment options
