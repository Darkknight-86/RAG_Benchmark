# AWS CLI Basics

### 0. Install
```
pip3 install awscli
```

### 1. Set up credientals
```
aws configure
```
Follow the prompts given, make sure you properly set the region (it matters!!!).
Set the output format to `json`.

### 2. Helpful Commands
```shell
# List contents of our bucket
aws s3 ls s3://ragproject-store/papers/

# Print a file to the terminal
aws s3 cp s3://ragproject-store/papers/something.txt -


# Delete all papers
aws s3 rm s3://ragproject-store/papers/ --recursive

# Delete all papers (except Ronnie's test document)
aws s3 rm s3://ragproject-store/papers/ --recursive --exclude "scores.txt"
```

# Start Virtual Environvment

```shell
# windows via installed python
python -m poetry install

# OR assuming you have poetry installed systemwide
poetry install
```

# Scraping the PDFs then Uploading to S3

```shell
# after your virtual environment is complete...
poetry run python src/rag/main.py
```

<!-- 


currently toml is not locked but should be and set for versions >= 3.11 python -->
