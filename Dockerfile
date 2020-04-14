FROM python:3.7-alpine
ADD server.py /
CMD ["python", "./server.py"]