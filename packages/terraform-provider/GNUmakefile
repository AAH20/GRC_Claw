BINARY        = terraform-provider-grc
VERSION       ?= 0.8.0
OS_ARCH       = $(shell go env GOOS)_$(shell go env GOARCH)
INSTALL_PATH  = ~/.terraform.d/plugins/registry.terraform.io/a2zsoc/grc/$(VERSION)/$(OS_ARCH)

default: build

## build: compile the provider binary
build:
	go build -o $(BINARY) .

## install: build and install the provider locally for Terraform testing
install: build
	mkdir -p $(INSTALL_PATH)
	mv $(BINARY) $(INSTALL_PATH)/$(BINARY)_v$(VERSION)

## test: run unit tests
test:
	go test ./... -v -count=1 -timeout 120s

## testacc: run acceptance tests (requires TF_ACC=1 and a live API key)
testacc:
	TF_ACC=1 go test ./... -v -count=1 -timeout 120s

## lint: run golangci-lint (install separately: https://golangci-lint.run)
lint:
	golangci-lint run ./...

## clean: remove compiled artifacts
clean:
	rm -f $(BINARY)

.PHONY: build install test testacc lint clean
