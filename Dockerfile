FROM python:3.11.7-bullseye

RUN mkdir /app
WORKDIR /app
ADD requirements.txt /app/
RUN pip install -r requirements.txt
ADD cf2/ /app/cf2/
# RUN pip install npTDMS[hdf,pandas,thermocouple_scaling] numpy dash
ADD app.py /app/
ADD tdms_conversion.py /app/

ENTRYPOINT [ "python" ]
CMD ["app.py"]