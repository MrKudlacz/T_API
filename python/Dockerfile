# our base image
FROM python:3.9.2

# upgrade pip
#RUN pip install --upgrade pip

# install Python modules needed by the Python app
COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r /usr/src/app/requirements.txt

# copy files required for the app to run
COPY main.py /usr/src/app/
COPY logger.py /usr/src/app/
COPY log.txt /usr/src/app/
COPY data/orders.json /usr/src/app/data/
COPY data/passwords.json /usr/src/app/data/

# tell the port number the container should expose
EXPOSE 5000

# run the application
CMD ["python", "/usr/src/app/main.py"]
