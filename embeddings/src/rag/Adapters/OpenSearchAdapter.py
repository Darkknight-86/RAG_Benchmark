from opensearchpy import OpenSearch, RequestsHttpConnection
from opensearchpy.exceptions import NotFoundError
import docker
import time
import os
import uuid
import numpy as np
import requests
from .VectorStoreAdapter import VectorStoreAdapter

class OpenSearchAdapter(VectorStoreAdapter):
    def __init__(self, index_name="rag_embeddings"):
        self.ensure_local_opensearch()

        self.host = os.getenv("OPENSEARCH_HOST", "localhost")
        self.port = int(os.getenv("OPENSEARCH_PORT", 9200))
        self.auth = (
            os.getenv("OPENSEARCH_USER", "admin"),
            os.getenv("OPENSEARCH_PASS", os.getenv("OPENSEARCH_INITIAL_ADMIN_PASSWORD", "admin"))
        )
        self.index_name = index_name

        self.client = OpenSearch(
            hosts=[{"host": self.host, "port": self.port}],
            http_auth=self.auth,
            use_ssl=False,
            verify_certs=False,
            connection_class=RequestsHttpConnection
        )

        self._create_index_if_not_exists()

    def _create_index_if_not_exists(self):
        if not self.client.indices.exists(index=self.index_name):
            self.client.indices.create(
                index=self.index_name,
                body={
                    "mappings": {
                        "properties": {
                            "embedding": {"type": "dense_vector", "dims": 768},
                            "text": {"type": "text"},
                            "metadata": {"type": "object"}
                        }
                    }
                }
            )

    def add_embedding(self, embeddings, texts, metadata_list):
        if not isinstance(embeddings[0], (list, np.ndarray)):
            # Single vector case
            embeddings = [embeddings]
            texts = [texts]
            metadata_list = [metadata_list]

        for i in range(len(embeddings)):
            doc = {
                "embedding": embeddings[i],
                "text": texts[i],
                "metadata": metadata_list[i]
            }
            self.client.index(index=self.index_name, id=str(uuid.uuid4()), body=doc)

    def ensure_local_opensearch(self, container_name="local-opensearch", port=9200):
        client = docker.from_env()

        # Check if already running
        try:
            container = client.containers.get(container_name)
            if container.status != "running":
                print("🟡 Starting existing OpenSearch container...")
                container.start()
            else:
                print("🟢 OpenSearch is already running.")
            return
        except docker.errors.NotFound:
            print("🔧 Creating a new OpenSearch container...")

        # Pull image if not available locally
        try:
            client.images.get("opensearchproject/opensearch:2.11.1")
        except docker.errors.ImageNotFound:
            print("📦 Pulling OpenSearch image...")
            client.images.pull("opensearchproject/opensearch:2.11.1")

        # Create and run new container
        client.containers.run(
            "opensearchproject/opensearch:2.11.1",
            name=container_name,
            ports={"9200/tcp": port, "9600/tcp": 9600},
            environment={
                "discovery.type": os.getenv("discovery_type", "single-node"),
                "plugins.security.disabled": "true",
                "OPENSEARCH_JAVA_OPTS": os.getenv("OPENSEARCH_JAVA_OPTS", "-Xms512m -Xmx512m"),
                "OPENSEARCH_INITIAL_ADMIN_PASSWORD": os.getenv("OPENSEARCH_INITIAL_ADMIN_PASSWORD", "admin")
            },
            detach=True,
            remove=False,
            tty=True
        )

        # Wait for OpenSearch to be ready
        print("⏳ Waiting for OpenSearch to become ready...")
        for _ in range(30):
            try:
                response = requests.get(f"http://localhost:{port}")
                if response.ok:
                    print("✅ OpenSearch is ready.")
                    return
            except requests.ConnectionError:
                pass
            time.sleep(1)

        print("❌ OpenSearch failed to start within timeout.")