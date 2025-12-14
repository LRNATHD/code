#!/bin/bash
set -e

# Check if we are running as root
if [ "$EUID" -ne 0 ]; then 
  echo "Please run as root (use 'wsl -u root ...')"
  exit 1
fi

echo "Starting setup for ch32fun development environment in WSL..."

# Update package lists
echo "Updating package lists..."
apt-get update

# Install dependencies
echo "Installing dependencies..."
# build-essential: make, gcc, etc.
# gcc-riscv64-unknown-elf: The RISC-V toolchain
# libusb-1.0-0-dev: For USB communication (minichlink)
# libudev-dev: Device management (minichlink)
# libconfuse-dev: Needed for some tools
# libnewlib-dev: For newlib (ch32fun)
apt-get install -y build-essential gcc-riscv64-unknown-elf libusb-1.0-0-dev libudev-dev libconfuse-dev libnewlib-dev

echo "----------------------------------------------------------------"
echo "Setup complete! You can now compile ch32fun projects."
echo "----------------------------------------------------------------"
