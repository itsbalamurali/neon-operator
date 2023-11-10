FROM python:3.11
COPY . /src
WORKDIR /src
RUN pip install -r requirements.txt
CMD kopf run -A ./main.py --verbose --standalone --log-format=full
