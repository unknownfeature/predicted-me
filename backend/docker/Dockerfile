FROM public.ecr.aws/lambda/python:3.12
ARG BACKEND_DIR
ARG SHARED_DIR
ARG FUNC_DIR
ARG LIB_DIR
ARG LIB_PATH=${BACKEND_DIR}/${LIB_DIR}
ARG FUNC_PATH=${BACKEND_DIR}/${FUNC_DIR}
ARG INSTALL_MYSQL
ARG REQS=requirements.txt

COPY $FUNC_DIR/index.py ${LAMBDA_TASK_ROOT}

RUN mkdir -p ${LAMBDA_TASK_ROOT}/backend/${LIB_DIR}
COPY ${LIB_PATH} ${LAMBDA_TASK_ROOT}/backend/${LIB_DIR}

RUN mkdir ${LAMBDA_TASK_ROOT}/shared
COPY ${SHARED_PATH}  ${LAMBDA_TASK_ROOT}/shared


RUN if [ -f "$FUNC_DIR/$REQS" ]; then \
        cp "$FUNC_DIR/$REQS ${LAMBDA_TASK_ROOT}/requirements.txt" \
    fi

RUN if [ -f "$FUNC_DIR/$REQS" ]; then \
    yum install -y pkgconfig \
    fi

RUN if [ -n "$INSTALL_MYSQL" ]; then \
    yum install -y gcc python3-devel mysql-devel mysql \
    fi

RUN if [ -f "$FUNC_DIR/$REQS" ]; then \
    pip3 install -r $LAMBDA_TASK_ROOT/requirements.txt \
    fi


ENTRYPOINT ["/lambda-entrypoint.sh", "index.handler"]