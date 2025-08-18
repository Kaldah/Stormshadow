# Makefile for eBPF SIP Spoofer
# This makefile helps compile the eBPF program for packet spoofing

CC = clang
CFLAGS = -O2 -target bpf -Wall -Wextra -g
INCLUDES = -I/usr/include -I/usr/include/linux

# Source and target files
SRC = ebpf_spoofer.c
OBJ = ebpf_spoofer.o

# Default target
all: $(OBJ)

# Compile eBPF object file with BTF information
$(OBJ): $(SRC)
	@echo "Compiling eBPF program with BTF..."
	$(CC) $(CFLAGS) $(INCLUDES) -c $< -o $@
	@echo "eBPF program compiled successfully: $@"

# Clean compiled files
clean:
	@echo "Cleaning compiled files..."
	rm -f $(OBJ)
	@echo "Clean completed"

# Install dependencies (requires root)
install-deps:
	@echo "Installing eBPF development dependencies..."
	@echo "This requires root privileges and may vary by distribution"
	@if command -v apt-get >/dev/null 2>&1; then \
		sudo apt-get update && sudo apt-get install -y clang llvm libbpf-dev linux-headers-$$(uname -r); \
	elif command -v yum >/dev/null 2>&1; then \
		sudo yum install -y clang llvm libbpf-devel kernel-headers; \
	elif command -v dnf >/dev/null 2>&1; then \
		sudo dnf install -y clang llvm libbpf-devel kernel-headers; \
	else \
		echo "Please install clang, llvm, libbpf-dev/libbpf-devel, and kernel headers manually"; \
	fi

# Check if required tools are available
check-deps:
	@echo "Checking eBPF development dependencies..."
	@command -v clang >/dev/null 2>&1 || { echo "clang not found. Please install clang."; exit 1; }
	@echo "✓ clang found"
	@test -f /usr/include/linux/bpf.h || { echo "Linux BPF headers not found. Please install kernel headers."; exit 1; }
	@echo "✓ Linux BPF headers found"
	@echo "All dependencies satisfied!"

# Help target
help:
	@echo "eBPF SIP Spoofer Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  all          - Compile the eBPF program (default)"
	@echo "  clean        - Remove compiled files"
	@echo "  check-deps   - Check if required dependencies are installed"
	@echo "  install-deps - Install required dependencies (requires root)"
	@echo "  help         - Show this help message"
	@echo ""
	@echo "Files:"
	@echo "  Source: $(SRC)"
	@echo "  Object: $(OBJ)"

.PHONY: all clean install-deps check-deps help
