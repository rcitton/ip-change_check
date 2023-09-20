FROM python:3.11.5-slim-bookworm
ARG BUILD_DATE
LABEL \
  maintainer="Ruggero Citton <rcitton@gmail.com>" \
  authors="Ruggero Citton <rcitton@gmail.com>" \
  title="IPChange-Check" \
  description="Module to notify user if public IP change has occured" \
  created=$BUILD_DATE

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Rome

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Set prompt
RUN echo 'export PS1="[🌐 \e[0;34m\h\e[0m \w]# "' >> /root/.bashrc

# Install dependencies
RUN apt-get update
RUN apt-get -q -y install --no-install-recommends apt-utils cron tzdata

# Clean up
RUN apt-get -q -y autoremove && apt-get -q -y clean
RUN rm -rf /var/lib/apt/lists/*


# Install python requirements
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy and final setup
COPY notifications notifications
COPY initial_config.py initial_config.py
COPY IP-check.py IP-check.py
COPY notification_test.py notification_test.py
COPY README.md README.md

COPY entrypoint.sh entrypoint.sh
RUN chmod +x /app/entrypoint.sh


# Execution
ENTRYPOINT ["/app/entrypoint.sh"]
#CMD ["bash"]
