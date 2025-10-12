FROM public.ecr.aws/lambda/python:3.12
ARG BACKEND_DIR=backend
ARG SHARED_DIR=shared
ARG FUNC_ROOT_DIR=functions
ARG FUNC_DIR
ARG LIB_DIR=lib
ARG REQS=requirements.txt
ARG VARS=variables.py
ARG CONST=constants.py

COPY ${BACKEND_DIR}/${FUNC_ROOT_DIR}/$FUNC_DIR/index.py ${LAMBDA_TASK_ROOT}

RUN mkdir -p ${LAMBDA_TASK_ROOT}/${BACKEND_DIR}/${LIB_DIR}
RUN touch ${LAMBDA_TASK_ROOT}/${BACKEND_DIR}/__init__.py
RUN touch ${LAMBDA_TASK_ROOT}/${BACKEND_DIR}/${LIB_DIR}/__init__.py
COPY ${BACKEND_DIR}/${LIB_DIR}/* ${LAMBDA_TASK_ROOT}/${BACKEND_DIR}/${LIB_DIR}/

RUN mkdir ${LAMBDA_TASK_ROOT}/${SHARED_DIR}
RUN touch ${LAMBDA_TASK_ROOT}/${SHARED_DIR}/__init__.py
COPY ${SHARED_DIR}/${VARS}  ${LAMBDA_TASK_ROOT}/${SHARED_DIR}/${VARS}
COPY ${SHARED_DIR}/${CONST}  ${LAMBDA_TASK_ROOT}/${SHARED_DIR}/${CONST}

COPY ${REQS} ${LAMBDA_TASK_ROOT}/${REQS}

RUN dnf update && dnf install -y gcc pkgconf pkgconf-pkg-config python3-devel

RUN pip3 install -r ${LAMBDA_TASK_ROOT}/${REQS}
RUN if [ -f "${BACKEND_DIR}/${FUNC_ROOT_DIR}/${FUNC_DIR}/${REQS}" ]; then \
        cp -f "${BACKEND_DIR}/${FUNC_ROOT_DIR}/${FUNC_DIR}/${REQS}" "${LAMBDA_TASK_ROOT}/${REQS}" && \
        pip3 install -r "$LAMBDA_TASK_ROOT/${REQS}"; \
    fi


ENTRYPOINT ["/lambda-entrypoint.sh", "index.handler"]