FROM public.ecr.aws/lambda/python:3.12
RUN yum install -y  python3-devel pkgconfig
COPY index.py ${LAMBDA_TASK_ROOT}
COPY ../../../lib/* ${LAMBDA_TASK_ROOT}
RUN pip3 install -r requirements.txt
ENTRYPOINT ["/lambda-entrypoint.sh", "index.handler"]
