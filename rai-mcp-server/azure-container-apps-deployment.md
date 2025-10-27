# Azure Container Apps Deployment Guide

> Currently, this server is deployed to Azure using Tezan's account. 
>
> It is available at https://mcp-server-app.icycliff-ccab3350.eastus.azurecontainerapps.io/mcp
>
> To deploy any updates, make code changes & reach out to Tezan (`tezansahu`) to perform the "Update Server Code" steps

## Prerequisites
1. Install Azure CLI: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli
2. Install Docker Desktop (for local testing)

## Deployment Steps

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

### 4. Build and Push Docker Image
```bash
# Login to registry
az acr login --name tezanmcpserverregistry

# Build and push image
docker build -t tezanmcpserverregistry.azurecr.io/mcp-server:latest .
docker push tezanmcpserverregistry.azurecr.io/mcp-server:latest
```

### 5. Create Container Apps Environment
```bash
az containerapp env create --name mcp-env --resource-group rg-mcp-server --location eastus
```

### 6. Deploy Container App

Get the password & copy it
```bash
az acr credential show --name tezanmcpserverregistry --query passwords[0].value -o tsv
```

Deploy with the new image:
```bash
az containerapp create --name mcp-server-app --resource-group rg-mcp-server --environment mcp-env --image tezanmcpserverregistry.azurecr.io/mcp-server:latest --target-port 8000 --ingress external --registry-server tezanmcpserverregistry.azurecr.io --registry-username tezanmcpserverregistry --registry-password {copied password}
```

## Update Server Code

1. Update the code in `server.py`

2. Repeat Steps 4 and 6 from above

## Your MCP server will be accessible at the provided URL after deployment.