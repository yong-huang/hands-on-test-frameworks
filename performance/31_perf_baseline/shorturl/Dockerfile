# 单阶段：静态二进制直接在 golang-alpine 里跑，省掉运行时基础镜像
FROM golang:1.23-alpine
WORKDIR /src
ENV GOFLAGS=-mod=vendor
# 依赖已 vendor 进仓库：构建容器不需要访问外网
COPY vendor vendor
COPY go.mod ./
COPY main.go .
RUN CGO_ENABLED=0 go build -o /usr/local/bin/shorturl .
CMD ["shorturl"]
