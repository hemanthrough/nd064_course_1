FROM python:3.8

WORKDIR /app

copy  . /app 

# import dependencies and build the application 
RUN pip install -r requirements.txt
RUN python init_db.py
EXPOSE 3111
CMD ["python","app.py"]




