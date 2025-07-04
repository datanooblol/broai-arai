FROM python:3.13-slim AS build

WORKDIR /build

# 🔧 Install necessary tools to build sentencepiece
RUN apt-get update && apt-get install -y \
    build-essential \
    g++ \
    cmake \
    make \
    bash \
    libprotobuf-dev \
    protobuf-compiler \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir --target ./python -r requirements.txt

# Stage 2: Final slim Lambda image
FROM public.ecr.aws/lambda/python:3.13
COPY --from=build /build/python ${LAMBDA_TASK_ROOT}
# ✅ Copy lambda_function.py directly to the root
COPY ./app/lambda_function.py ${LAMBDA_TASK_ROOT}/lambda_function.py

# ✅ Copy package/ directory from backend root (auto-sync)
COPY ./app/package ${LAMBDA_TASK_ROOT}/package

# Lambda entry point (root level handler)
CMD ["lambda_function.lambda_handler"]