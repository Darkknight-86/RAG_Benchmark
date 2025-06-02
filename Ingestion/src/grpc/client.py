import grpc
import rawdataingestion_pb2
import rawdataingestion_pb2_grpc

def run():
    # Create a channel to the server
    with grpc.insecure_channel('localhost:50051') as channel:
        # Create a stub (client)
        stub = rawdataingestion_pb2_grpc.PipelineServiceStub(channel)
        
        # Prepare parameters for the pipeline
        params = {
            "csv_filename": "arxiv_papers_metadata.csv",
            "max_results": "10",
            "years": "5",
            "output_dir": "arxiv_pdfs",
            "clean_existing": "true"
        }
        
        # Create a request with generic params
        request = rawdataingestion_pb2.PipelineRequest(params=params)
        
        # Call the pipeline and stream status updates
        responses = stub.ExecutePipeline(request)
        print("Pipeline process output:")
        for status in responses:
            print(f"[{status.step}] {status.message}")
            if status.is_error:
                print(f"Error: {status.error_message}")
            if status.is_complete:
                print("Pipeline execution finished.")

if __name__ == '__main__':
    run()