ARG BUILD_FROM
FROM $BUILD_FROM

LABEL \
  io.hass.name="Ambientika MQTT Bridge" \
  io.hass.description="MQTT bridge for Ambientika ventilation units" \
  io.hass.arch="${BUILD_ARCH}" \
  io.hass.type="addon" \
  io.hass.version="${BUILD_VERSION}" \
  maintainer="Ambientika / SUEDWIND"

# Install Python dependencies
RUN apk add --no-cache python3 py3-pip

# Install bridge dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Copy bridge script
COPY bridge.py /app/bridge.py

# Copy startup script
COPY run.sh /run.sh
RUN chmod +x /run.sh

CMD [ "/run.sh" ]
