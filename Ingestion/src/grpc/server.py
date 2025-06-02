# grpc/src/grpc/server.py
import sys
import os
from io import StringIO
import rawdataingestion_pb2_grpc as pb2_grpc  # This is the generated file
import rawdataingestion_pb2 as pb2            # This is the generated file
import grpc
from concurrent import futures

# Add the RAG directory to Python path
rag_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'RAG', 'src', 'rag'))
sys.path.append(rag_path)

print(f"Looking for RAG modules at: {rag_path}")

try:
    from main import execute  # Import directly, not as rag.src.rag.main
    print("Successfully imported RAG modules")
except ImportError as e:
    print(f"Error importing RAG modules: {e}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path additions: {rag_path}")
    sys.exit(1)

class PipelineService(pb2_grpc.PipelineServiceServicer):
    
    def ExecutePipeline(self, request, context):
        try:
            yield pb2.PipelineStatus(
                step="starting",
                message="Starting RAG pipeline execution...",
                is_complete=False,
                is_error=False
            )
            
            params = request.params
            csv_filename = params.get("csv_filename", "arxiv_papers_metadata.csv")
            max_results = int(params["max_results"]) if "max_results" in params else 100
            years = int(params["years"]) if "years" in params else 2
            output_dir = params.get("output_dir", "arxiv_pdfs")
            clean_existing = params.get("clean_existing", "true").lower() == "true"

            old_stdout = sys.stdout
            sys.stdout = captured_output = StringIO()
            
            try:
                # Pass all arguments to execute
                execute(
                    csv_filename=csv_filename,
                    max_results=max_results,
                    years=years,
                    output_dir=output_dir,
                    clean_existing=clean_existing
                )
                captured_text = captured_output.getvalue()
                if captured_text.strip():
                    for line in captured_text.strip().split('\n'):
                        yield pb2.PipelineStatus(
                            step="processing",
                            message=line,
                            is_complete=False,
                            is_error=False
                        )
            finally:
                sys.stdout = old_stdout
            
            yield pb2.PipelineStatus(
                step="complete",
                message="Pipeline execution completed successfully",
                is_complete=True,
                is_error=False
            )
            
        except Exception as e:
            yield pb2.PipelineStatus(
                step="error",
                message="Pipeline failed",
                is_complete=True,
                is_error=True,
                error_message=str(e)
            )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb2_grpc.add_PipelineServiceServicer_to_server(PipelineService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Server started on port 50051...")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()