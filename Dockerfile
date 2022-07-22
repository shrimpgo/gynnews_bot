FROM alpine:3.16

ENV TZ=America/Sao_Paulo

RUN apk update && apk add python3 py3-pip build-base python3-dev
RUN mkdir /app
WORKDIR /app
ADD *txt bot.conf gynnews-bot.py /app/

# Leave commented this line below if you never run this instance before
#ADD .database /app/

RUN pip3 install --upgrade pip && pip3 install -r requirements.txt

CMD python3 gynnews-bot.py
