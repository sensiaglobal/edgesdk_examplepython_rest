FROM python:3.12-slim AS base
# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-dotnet-configure-containers
RUN useradd -d /app -M -s /sbin/nologin -u 5678 -U appuser
USER appuser:appuser

FROM base AS slim
# Environment variable needed for read-only filesystem
ENV COMPlus_EnableDiagnostics=0

WORKDIR /app
COPY requirements.txt .
RUN pip3 install -r requirements.txt && pip3 install typing-extensions --upgrade

RUN mkdir classes/ & \
mkdir config/ & \
mkdir lib/ & \
mkdir data/ & 

COPY --chown=appuser:appuser *.py ./ 
COPY --chown=appuser:appuser config/ config/
COPY --chown=appuser:appuser classes/ classes/
COPY --chown=appuser:appuser lib/ lib/
COPY --chown=appuser:appuser data/ data/

COPY --chown=appuser:appuser entry_point.sh .
RUN chmod +x entry_point.sh
USER root:root
RUN install -o appuser -g appuser -d -m 0755 /tmp
RUN install -o appuser -g appuser -d -m 0755 /app/config
USER appuser:appuser
ENTRYPOINT ["./entry_point.sh"]
#ENTRYPOINT ["/usr/bin/tail", "-f", "/dev/null"]

LABEL org.opencontainers.image.authors="NGRTU Team <ngrtuteam@sensiaglobal.com>" \
      org.opencontainers.image.vendor="Sensia Global" \
      org.opencontainers.image.url="https://www.sensiaglobal.com/" \
      org.opencontainers.image.license="Propietary" \
      com.sensiaglobal.image.artifacts.source="sensia-edge-docker-dev"



