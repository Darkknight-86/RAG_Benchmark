import llamap, loader

def execute(
    csv_filename="arxiv_papers_metadata.csv",
    max_results=100,
    years=2,
    output_dir="arxiv_pdfs",
    clean_existing=True
):
    print("Step one: scraping PDFs...")
    loader.scrape_arxiv_papers(
        years=years,
        max_results=max_results,
        output_dir=output_dir,
        csv_filename=csv_filename,
        clean_existing=clean_existing
    )
    print("Step one complete: scraped PDFs")
    print("Step two: convert exported PDFs to text")
    print(f"Starting to process PDFs from {csv_filename}")
    llamap.process_csv_and_pdfs(csv_filename)
    print("Step two complete, check your S3 bucket.")

if __name__ == "__main__":
    execute()