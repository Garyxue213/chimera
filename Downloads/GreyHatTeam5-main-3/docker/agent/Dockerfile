FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    net-tools \
    netcat-traditional \
    nmap \
    sqlmap \
    file \
    binutils \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install radare2 from GitHub
RUN git clone --depth 1 https://github.com/radareorg/radare2 /tmp/radare2 && \
    cd /tmp/radare2 && \
    sys/install.sh && \
    cd / && \
    rm -rf /tmp/radare2

# Copy requirements and install Python dependencies
COPY pyproject.toml /app/
RUN pip install --no-cache-dir -e .

# Copy the agent code
COPY agent/ /app/agent/
COPY helper/ /app/helper/
COPY mcp_tools/ /app/mcp_tools/
COPY docker/agent/run_agent.py /app/

CMD ["python", "run_agent.py"]