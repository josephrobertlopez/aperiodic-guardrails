#!/bin/bash
# Recover NVIDIA GPU from "Unable to determine the device handle" lockup
# Usually caused by suspend/resume not releasing the GPU cleanly.
#
# Safe-ish: stops ollama, resets nvidia kernel modules, restarts ollama.
# Reversible: if it fails, a reboot will always recover.
#
# Run as: bash scripts/fix_gpu.sh

set -e

echo "=== before ==="
echo "--- nvidia-smi ---"
nvidia-smi 2>&1 | head -5 || true
echo "--- ollama loaded ---"
curl -s --max-time 3 http://localhost:11434/api/ps | jq -r '.models[]? | "\(.name) ctx=\(.size_vram)"' 2>/dev/null || echo "ollama unreachable"
echo ""

echo "=== stopping ollama ==="
sudo systemctl stop ollama
sleep 2

echo "=== unloading nvidia modules ==="
# order matters: dependents first
sudo rmmod nvidia_uvm 2>&1 || echo "  nvidia_uvm: in use or already unloaded"
sudo rmmod nvidia_drm 2>&1 || echo "  nvidia_drm: in use (display server holding it — may need to drop to TTY)"
sudo rmmod nvidia_modeset 2>&1 || echo "  nvidia_modeset: in use"
sudo rmmod nvidia 2>&1 || echo "  nvidia: in use"

echo "=== reloading nvidia modules ==="
sudo modprobe nvidia
sudo modprobe nvidia_modeset
sudo modprobe nvidia_uvm
sleep 1

echo "=== after reset ==="
nvidia-smi 2>&1 | head -10

echo "=== restarting ollama ==="
sudo systemctl start ollama
sleep 3
echo "=== ollama version ==="
curl -s --max-time 5 http://localhost:11434/api/version | jq -r '.'

echo ""
echo "=== test 14b quick gen ==="
time curl -s --max-time 60 http://localhost:11434/api/generate -d '{"model":"qwen2.5-coder:14b","prompt":"say READY","stream":false}' | jq -r '.response // .error // "EMPTY"'

echo ""
echo "=== check KV cache location in next-load logs ==="
sudo journalctl -u ollama -n 20 --no-pager | grep -E "KV buffer|n-gpu-layers|VRAM"

echo ""
echo "Done. If KV buffer still says 'CPU KV', GPU is not being used — likely the kernel module reset didn't take and a reboot is needed."
