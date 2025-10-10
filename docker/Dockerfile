FROM public.ecr.aws/lambda/python:3.12
ARG BACKEND_DIR
ARG SHARED_PATH
ARG FUNC_DIR
ARG LIB_DIR
ARG LIB_PATH=${BACKEND_DIR}/${LIB_DIR}
ARG FUNC_PATH=${BACKEND_DIR}/${FUNC_DIR}
ARG REQS=requirements.txt
ARG FUNC_REQS=func_requirements.txt
COPY $FUNC_DIR/index.py ${LAMBDA_TASK_ROOT}

RUN mkdir -p ${LAMBDA_TASK_ROOT}/backend/${LIB_DIR}
RUN touch ${LAMBDA_TASK_ROOT}/backend/__init__.py
COPY ${LIB_PATH} ${LAMBDA_TASK_ROOT}/backend/${LIB_DIR}

RUN mkdir ${LAMBDA_TASK_ROOT}/shared
COPY ${SHARED_PATH}  ${LAMBDA_TASK_ROOT}/shared

COPY ${REQS} ${LAMBDA_TASK_ROOT}/${REQS}
RUN yum install -y gcc python3-devel mysql-devel mysql
RUN  pip3 install -r $LAMBDA_TASK_ROOT/${REQS}
RUN if [ -f "$FUNC_DIR/$REQS" ]; then \
        cp "$FUNC_DIR/$REQS ${LAMBDA_TASK_ROOT}/${FUNC_REQS}" \
    fi

RUN if [ -f "$FUNC_DIR/$REQS" ]; then \
        RUN  pip3 install -r $LAMBDA_TASK_ROOT/${FUNC_REQS}"  \
    fi
ENTRYPOINT ["/lambda-entrypoint.sh", "index.handler"]