# Configuration File Examples

This directory contains example configuration files for SOGS authentication.

## Files

### `snowflake_config.json`
Example JSON configuration file with multiple connection profiles.

### `snowflake_config.toml`
Example TOML configuration file with multiple connection profiles.

## Usage

1. **Copy the example file:**
   ```bash
   cp snowflake_config.json my_snowflake_config.json
   # or
   cp snowflake_config.toml my_snowflake_config.toml
   ```

2. **Edit the copied file** with your actual credentials:
   - Replace `abc12345` with your Snowflake account identifier
   - Replace `your_username` with your Snowflake username
   - Add your password or private key path
   - Update warehouse, database, schema, and role as needed

3. **Protect the file:**
   ```bash
   chmod 600 my_snowflake_config.json
   ```

4. **Use in SOGS:**
   - Via Web UI: Select "Configuration File" tab and provide the path
   - Via API: POST to `/api/credentials/configure-from-file`

## Configuration File Format

### Required Fields
- `account` - Snowflake account identifier
- `user` - Snowflake username
- **Either** `password` **or** `private_key_path` (choose one authentication method)

### Optional Fields
- `warehouse` - Default warehouse
- `database` - Default database
- `schema` - Default schema
- `role` - Default role
- `private_key_passphrase` - Passphrase for encrypted private keys

## Multiple Connection Profiles

Both JSON and TOML formats support multiple named connection profiles:

```json
{
  "default": { ... },
  "production": { ... },
  "development": { ... }
}
```

Specify the connection name when connecting:
- In Web UI: Enter "production" in the "Connection Name" field
- Via API: Include `"connection_name": "production"` in the request

## Security Notes

⚠️ **Never commit actual credentials to version control!**

- Add your config files to `.gitignore`
- Use environment-specific naming: `snowflake.dev.json`, `snowflake.prod.json`
- Prefer private key authentication over passwords for production
- Set restrictive file permissions: `chmod 600 config.json`

## See Also

- [AUTHENTICATION.md](../AUTHENTICATION.md) - Complete authentication guide
- [README.md](../README.md) - Main documentation
- [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) - Connection troubleshooting
