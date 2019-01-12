FROM mongo


RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY darvazeh .
RUN chmod 400 /usr/src/app/darvazeh
RUN chown mongodb:mongodb /usr/src/app/darvazeh
