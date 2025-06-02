#!/usr/bin/env python3
import os
import subprocess
from pathlib import Path

def generate_grpc_code():
    """Generate gRPC code from proto files."""
    # Get the project root directory
    project_root = Path(__file__).parent

    # Define paths
    proto_dir = project_root / "protos"
    output_dir = project_root / "src" / "api_gateway" / "grpc"

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Generate gRPC code
    proto_file = proto_dir / "rag_service.proto"

    # Command to generate Python code
    cmd = [
        "python", "-m", "grpc_tools.protoc",
        f"--proto_path={proto_dir}",
        f"--python_out={output_dir}",
        f"--grpc_python_out={output_dir}",
        str(proto_file)
    ]

    try:
        subprocess.run(cmd, check=True)
        print(f"Successfully generated gRPC code in {output_dir}")

        # Create __init__.py if it doesn't exist
        init_file = output_dir / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            print(f"Created {init_file}")

    except subprocess.CalledProcessError as e:
        print(f"Error generating gRPC code: {e}")
        raise

if __name__ == "__main__":
    generate_grpc_code()