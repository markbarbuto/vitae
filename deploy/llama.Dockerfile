# Runs the llama.cpp v0.8.0 build that Phase 0 compiled on the VM with native CPU flags, mounted at /opt/llama.
FROM ubuntu:24.04
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 curl && rm -rf /var/lib/apt/lists/*
ENV LD_LIBRARY_PATH=/opt/llama
ENTRYPOINT ["/opt/llama/llama-server"]
