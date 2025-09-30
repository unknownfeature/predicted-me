FROM public.ecr.aws/lambda/python:3.12
ARG LIB_PATH=../../../lib
ARG SHARED_PATH=../../../..
ARG FUNC_DIR=.
ARG INSTALL_MYSQL
ARG REQS=requirements.txt

COPY $FUNC_DIR/index.py ${LAMBDA_TASK_ROOT}
COPY ${LIB_PATH} ${LAMBDA_TASK_ROOT}/lib/
COPY ${SHARED_PATH} ${SHARED_PATH}/shared/


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