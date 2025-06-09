# ASX Real-Time Market Data Streamer

## Note on Azure
The pipeline no longer uploads to Azure Blob Storage, and throughout there may be references to Azure. These are meant to be cleaned and deprecated in the future.

## Overview
This system streams real-time stock price data from the Australian Securities Exchange (ASX) for monitoring and analysis. You can use any stock that Yahoo supports, including crypto.

## Responsibilities

### 1. **Real-Time Data Collection**
- Connects to Yahoo Finance WebSocket API to receive live ticker updates
- Monitors multiple ASX-listed securities simultaneously
- Captures price movements, volume data, and percentage changes in real-time

### 2. **Market Hours Management**
- Determines ASX trading status (open, closed, pre-market, post-market, weekend)
- Provides accurate Sydney timezone-based market hour calculations
- Regular trading hours: 10:00 AM - 4:00 PM Sydney time
- Pre-market: 7:00 AM - 10:00 AM
- Post-market: 4:00 PM - 5:00 PM

### 3. **Data Transformation**
- Converts raw WebSocket messages into standardized format
- Applies appropriate decimal precision based on price hints
- Converts epoch timestamps to ISO 8601 format
- Enriches data with market status information

### 4. **Data Processing**
- Processes incoming ticker data in real-time
- Formats data according to business requirements
- Implements unique identification for each data point

### 5. **Error Handling**
- Gracefully handles connection failures
- Provides detailed logging for debugging
- Maintains continuous operation despite individual errors

## Tech Stack

### **Core Technologies**

#### Python 3.x
- Primary programming language
- Leverages async capabilities for WebSocket connections

#### yliveticker
- Third-party library for Yahoo Finance WebSocket connections
- Provides real-time ticker data streaming
- Handles WebSocket connection management and reconnection

### **Data Processing Libraries**

#### pytz
- Timezone management for Sydney/Australia time
- Ensures accurate market hours calculations
- Handles daylight saving time transitions

#### datetime
- Date and time operations
- Market hours comparison
- Timestamp conversions

#### json
- JSON serialization for structured data
- Ensures data compatibility for downstream processing

### **Secret Management**

#### python-dotenv
- Environment variable management
- Secure credential storage
- Separates configuration from code

#### pathlib
- Cross-platform file path handling
- Robust path resolution for `.env` file location (`.env` located at root)

### **Data Format**

#### Input (WebSocket Message)
```json
{
    "id": "WBC.AX",
    "exchange": "ASX",
    "quoteType": 8,
    "price": 32.619998931884766,
    "timestamp": 1748931012000,
    "marketHours": 1,
    "changePercent": 1.3673045635223389,
    "dayVolume": 0,
    "change": 0.4399986267089844,
    "priceHint": 2
}
```

#### Output (Processed Format)
```json
{
    "security": "WBC.AX",
    "price": 32.62,
    "changePercent": 1.37,
    "tradeVolume": 0,
    "isMarketOpen": true,
    "marketStatus": "open",
    "timestamp": "2025-02-03T14:30:12"
}
```

### **Monitored Securities**
- QAN.AX (Qantas Airways)
- WOW.AX (Woolworths Group)
- COL.AX (Coles Group)
- TLS.AX (Telstra Corporation)
- JBH.AX (JB Hi-Fi)

## Architecture Flow

1. **WebSocket Connection** → yliveticker establishes persistent connection to Yahoo Finance
2. **Message Reception** → Real-time ticker updates received via callback
3. **Market Status Check** → Current ASX trading status determined
4. **Data Transformation** → Raw data formatted and enriched
5. **Processing** → Data processed according to business logic
6. **Logging** → Activity logged for monitoring

## Key Features

- **Real-time Processing**: Sub-second latency from market events
- **Timezone Aware**: Accurate Sydney time calculations for market hours
- **Continuous Operation**: Resilient to individual processing failures
- **Structured Data**: Consistent format for easy downstream processing
- **Multi-ticker Support**: Monitors multiple securities simultaneously