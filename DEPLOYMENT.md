# MCP Servers Deployment Guide

This guide provides instructions for deploying MCP servers to Azure Container Apps using Azure Container Registry.

## Prerequisites

1. **Azure CLI**: Install from https://docs.microsoft.com/en-us/cli/azure/install-azure-cli
2. **Docker Desktop**: For local testing and building images
3. **Azure Account**: With appropriate permissions to create resources

## Initial Azure Setup (One-time)

### 1. Login to Azure
```bash
az login
```

### 2. Create Resource Group
```bash
az group create --name rg-mcp-server --location eastus
```

### 3. Create Container Registry
```bash
az acr create --resource-group rg-mcp-server --name tezanmcpserverregistry --sku Basic --admin-enabled true
```

### 4. Create Container Apps Environment
```bash
az containerapp env create --name mcp-env --resource-group rg-mcp-server --location eastus
```

## Deploying a New MCP Server

### Step 1: Prepare Your MCP Server

1. **Create a Dockerfile** in your server directory:
   ```dockerfile
   FROM python:3.11-slim
   
   WORKDIR /app
   
   # Copy requirements first for better caching
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   # Copy application code
   COPY server.py .
   # Copy any additional files your server needs
   # COPY data.csv .
   # COPY .env .
   
   # Expose the port your server uses
   EXPOSE 8000
   
   # Run the server
   CMD ["python", "server.py"]
   ```

2. **Update the Dockerfile** based on your server's specific needs:
   - Change the port number in `EXPOSE` to match your server's port
   - Add any additional files your server needs (CSV files, config files, etc.)
   - Update the `CMD` if your main server file has a different name

### Step 2: Build and Push Docker Image

```bash
# Navigate to your server directory
cd path/to/your-mcp-server

# Login to registry
az acr login --name tezanmcpserverregistry

# Build and push image (use a descriptive image name)
docker build -t tezanmcpserverregistry.azurecr.io/your-server-name:latest .
docker push tezanmcpserverregistry.azurecr.io/your-server-name:latest
```

### Step 3: Deploy Container App

Get the registry password:
```bash
az acr credential show --name tezanmcpserverregistry --query passwords[0].value -o tsv
```

Deploy your container app:
```bash
az containerapp create ^
  --name your-server-app ^
  --resource-group rg-mcp-server ^
  --environment mcp-env ^
  --image tezanmcpserverregistry.azurecr.io/your-server-name:latest ^
  --target-port YOUR_SERVER_PORT ^
  --ingress external ^
  --registry-server tezanmcpserverregistry.azurecr.io ^
  --registry-username tezanmcpserverregistry ^
  --registry-password {copied password}
```

**Replace the following placeholders:**
- `your-server-name`: A descriptive name for your server image (e.g., `mcp-auth-server`, `mcp-rai-server`)
- `your-server-app`: A descriptive name for your container app (e.g., `mcp-auth-server-app`)
- `YOUR_SERVER_PORT`: The port your server listens on (e.g., `8000`, `3001`)

### Step 4: Get Your Server URL

After deployment, get your server URL:
```bash
az containerapp show --name your-server-app --resource-group rg-mcp-server --query properties.configuration.ingress.fqdn -o tsv
```

Your MCP server will be accessible at: `https://[returned-fqdn]/mcp`

## Updating an Existing Server

To update an existing deployed server:

### 1. Update your code
Make changes to your server files.

### 2. Rebuild and push the image
```bash
# Navigate to your server directory
cd path/to/your-mcp-server

# Rebuild and push
docker build -t tezanmcpserverregistry.azurecr.io/your-server-name:latest .
docker push tezanmcpserverregistry.azurecr.io/your-server-name:latest
```

### 3. Update the container app
```bash
az containerapp update \
  --name your-server-app \
  --resource-group rg-mcp-server \
  --image tezanmcpserverregistry.azurecr.io/your-server-name:latest
```

## Server-Specific Information

### Current Deployed Servers

| Server Name | Image Name | Port | Container App | URL |
|-------------|------------|------|---------------|-----|
| RAI MCP Server | `mcp-server` | 8000 | `mcp-server-app` | https://mcp-server-app.icycliff-ccab3350.eastus.azurecontainerapps.io/mcp |
| Auth MCP Server | `mcp-auth-server` | 3001 | `mcp-auth-server-app` | https://mcp-auth-server-app.icycliff-ccab3350.eastus.azurecontainerapps.io/mcp |

### Server-Specific Notes

- **RAI MCP Server**: Requires `Responsible_AI_Content_Review.csv` file
- **Auth MCP Server**: Requires `.env` file with authentication configuration

## Troubleshooting

### Common Issues

1. **Build fails**: Check that all required files are present and Dockerfile syntax is correct
2. **Container won't start**: Check the logs with `az containerapp logs show --name your-server-app --resource-group rg-mcp-server`
3. **Server not accessible**: Verify the port number in both Dockerfile and container app configuration

### Useful Commands

```bash
# View container app logs
az containerapp logs show --name your-server-app --resource-group rg-mcp-server --follow

# List all container apps
az containerapp list --resource-group rg-mcp-server --output table

# Get container app details
az containerapp show --name your-server-app --resource-group rg-mcp-server

# Delete a container app
az containerapp delete --name your-server-app --resource-group rg-mcp-server
```

## Security Considerations

- Registry credentials are stored in the container app configuration
- Consider using managed identity for production deployments
- Ensure sensitive data is properly handled through environment variables
- Review ingress settings based on your security requirements

## Cost Management

- Container apps scale to zero when not in use
- Monitor usage through Azure Portal
- Consider resource limits for production deployments