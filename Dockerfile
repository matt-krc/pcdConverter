FROM ubuntu:22.04
RUN apt-get update \
    && apt-get install --fix-missing -y wget \
    && rm -rf /var/lib/apt/lists/*

RUN wget https://www.poweriso.com/poweriso-x64-1.6.tar.gz \
	&& mv poweriso-x64-1.6.tar.gz /usr/local/bin/ \
	&& cd /usr/local/bin \
	&& tar zxvf poweriso-x64-1.6.tar.gz \
	&& ln -s poweriso-x64 /usr/bin/

