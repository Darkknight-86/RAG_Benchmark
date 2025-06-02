import requests
import xml.etree.ElementTree as ET
import os
import time
from datetime import datetime, timedelta
import csv
import shutil


def scrape_arxiv_papers(years=2, max_results=100, output_dir="arxiv_pdfs", 
                       csv_filename="arxiv_papers_metadata.csv", clean_existing=True):
    """
    Main function to scrape arXiv papers and download PDFs.
    
    Args:
        years: Number of years to look back for papers
        max_results: Maximum number of results to fetch
        output_dir: Directory to save PDFs
        csv_filename: Name of the CSV file to save metadata
        clean_existing: Whether to remove existing files before starting
    
    Returns:
        dict: Summary statistics of the scraping process
    """
    # Clean existing data if requested
    if clean_existing:
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        if os.path.exists(csv_filename):
            os.remove(csv_filename)
    
    # Create output directory
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Define the arXiv query URL
    arxiv_url = f'http://export.arxiv.org/api/query?search_query=all:economics&start=0&max_results={max_results}'
    
    # Send request to arXiv API
    print(f"Fetching metadata from arXiv for {max_results} results within the last {years} years")
    response = requests.get(arxiv_url)
    
    if response.status_code != 200:
        print("Failed to retrieve metadata")
        return {"error": "Failed to retrieve metadata", "status_code": response.status_code}
    
    print("Successfully retrieved metadata from arXiv!")
    
    # Parse the XML response
    root = ET.fromstring(response.content)
    
    # CSV setup
    csv_headers = ["title", "author(s)", "published_date", "updated_date", "description", "scraped_date", "file_location"]
    
    # Statistics
    attempted_downloads = 0
    successful_downloads = 0
    download_start_time = time.time()
    
    # Open CSV file for writing
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_headers)
        writer.writeheader()
        
        # Calculate date threshold
        date_threshold = datetime.now() - timedelta(days=365 * years)
        
        # Process each entry
        for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
            # Get dates
            updated = entry.find('{http://www.w3.org/2005/Atom}updated').text
            published = entry.find('{http://www.w3.org/2005/Atom}published').text
            
            # Check if paper is within date range
            if updated or published:
                updated_date = datetime.strptime(updated, '%Y-%m-%dT%H:%M:%SZ')
                published_date = datetime.strptime(published, '%Y-%m-%dT%H:%M:%SZ')
                if updated_date < date_threshold and published_date < date_threshold:
                    continue
            
            # Get title
            title = entry.find('{http://www.w3.org/2005/Atom}title').text
            title = ' '.join(title.split())
            
            # Get authors
            authors = []
            for author in entry.findall('{http://www.w3.org/2005/Atom}author'):
                name = author.find('{http://www.w3.org/2005/Atom}name').text
                if name:
                    authors.append(name)
            authors_str = '|'.join(authors)
            
            # Get summary
            summary = entry.find('{http://www.w3.org/2005/Atom}summary').text
            summary = ' '.join(summary.split()) if summary else ""
            
            # Get PDF link
            pdf_link = None
            for link in entry.findall('{http://www.w3.org/2005/Atom}link'):
                if link.attrib.get('title') == 'pdf':
                    pdf_link = link.attrib.get('href')
                    break
            
            attempted_downloads += 1
            
            if pdf_link:
                # Create filename
                filename = title.replace(" ", "_").replace("/", "_").replace(":", "_").replace("?", "_") + ".pdf"
                if len(filename) > 255:
                    filename = filename[:250] + ".pdf"
                pdf_path = os.path.join(output_dir, filename)
                absolute_pdf_path = os.path.abspath(pdf_path)
                
                # Download PDF if it doesn't exist
                if not os.path.exists(pdf_path):
                    pdf_start_time = time.time()
                    pdf_response = requests.get(pdf_link)
                    pdf_end_time = time.time()
                    
                    if pdf_response.status_code == 200:
                        with open(pdf_path, 'wb') as f:
                            f.write(pdf_response.content)
                        print(f"Downloaded: {filename} (Time: {pdf_end_time - pdf_start_time:.2f} seconds)")
                        successful_downloads += 1
                    else:
                        print(f"Failed to download PDF for: {title}")
                        continue
                else:
                    print(f"Skipped (already exists): {filename}")
                    successful_downloads += 1
                
                # Write to CSV
                row_data = {
                    "title": title,
                    "author(s)": authors_str,
                    "published_date": published,
                    "updated_date": updated,
                    "description": summary,
                    "scraped_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "file_location": absolute_pdf_path
                }
                writer.writerow(row_data)
            else:
                print(f"No PDF link found for: {title}")
    
    # Calculate statistics
    download_end_time = time.time()
    total_time = download_end_time - download_start_time
    
    # Print summary
    print(f"\nSummary:")
    print(f"Attempted downloads: {attempted_downloads}")
    print(f"Successful downloads: {successful_downloads}")
    print(f"CSV file created: {csv_filename}")
    print(f"Time taken: {total_time:.2f} seconds")
    
    if successful_downloads > 0:
        print(f"Average time per document: {total_time / successful_downloads:.2f} seconds")
    
    # Return statistics
    return {
        "attempted_downloads": attempted_downloads,
        "successful_downloads": successful_downloads,
        "csv_filename": csv_filename,
        "output_dir": output_dir,
        "total_time": total_time
    }


# # Allow running as a script
# if __name__ == "__main__":
#     # Run with default parameters
#     results = scrape_arxiv_papers()
#     print("\n************** NEXT STEPS ************************")
#     print("Run the llamap.py file to parse the PDFs and upload them to Amazon S3")