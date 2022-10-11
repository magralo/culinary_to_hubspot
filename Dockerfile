FROM python:3.10-slim-buster


# Install manually all the missing libraries
RUN apt-get update

# Install Chrome
RUN apt install -y wget unzip
RUN apt-get install -y tzdata
#RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
#RUN dpkg -i google-chrome-stable_current_amd64.deb; apt-get -fy install
ARG CHROME_VERSION="105.0.5195.125-1"
RUN wget --no-verbose -O /tmp/chrome.deb https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_${CHROME_VERSION}_amd64.deb \
  && apt install -y /tmp/chrome.deb \
  && rm /tmp/chrome.deb




ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./
RUN pip install -r requirements.txt
# Requiered for server
#RUN pip install gunicorn  
#RUN pip install uvicorn 


CMD exec gunicorn --bind :$PORT --workers 1 --worker-class uvicorn.workers.UvicornWorker  --threads 8 main:app --timeout 900