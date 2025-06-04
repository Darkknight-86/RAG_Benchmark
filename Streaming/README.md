# Streaming Data

# Running the Pipeline
```shell
poetry lock
poetry install
poetry run python src\yahoo_ws.py
```

^^^ assuming you have your .env at the root folder up to date with Azure credentials.

### Schema for JSON Uploaded to Azure Blob Storage
```json
{
    'security': string,
    'price': float,
    'changePercent': float,
    'tradeVolume': int,
    'isMarketOpen': boolean,
    'marketStatus': string,
    'timestamp': iso_timestamp
}
```

![alt text](image.png)


### Azure CLI Configuration

```
# login via the web browser (you'll need to enter in a code on the microsoft website)
az login --use-device-code

# find the name of your "container" (just a fancy term for bucket)
az storage account list --query "[].name" --output tsv
```