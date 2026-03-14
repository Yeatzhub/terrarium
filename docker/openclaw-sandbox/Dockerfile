# OpenClaw Sandbox Image
# Minimal Debian with network tools for subagent tasks
FROM debian:bookworm-slim

# Install network and utility tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    python3 \
    python3-pip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user matching sandbox config
RUN useradd -m -u 1000 -s /bin/bash agent

# Set working directory
WORKDIR /workspace

# Run as non-root by default
USER agent

# Shell for exec commands
CMD ["/bin/bash"]