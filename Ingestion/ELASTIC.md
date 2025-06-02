# Open Search / Elastic Search Setup

```
docker run -d -p 9200:9200 -p 9600:9600 -e "discovery.type=single-node" -e "OPENSEARCH_INITIAL_ADMIN_PASSWORD=<YOUR_STRONG_PASSWORD_HERE>" opensearchproject/opensearch:latest
```

### Test Setup

```
curl -X GET "https://localhost:9200/_cluster/health?pretty" -k -u admin:<YOUR_STRONG_PASSWORD_HERE>
```

### Dataset

[Download Here](https://drive.proton.me/urls/AEFA701EJW#fwsMJc7GATHf)
