#!/bin/bash
# Post-reboot GPU recovery: kmod for this kernel exists but didn't auto-load
# on this boot. Modprobe them, restart Ollama, verify GPU inference.

set -e

echo "=== modprobe nvidia stack ==="
sudo modprobe nvidia 2>&1 || echo "  nvidia modprobe failed"
sudo modprobe nvidia_modeset 2>&1 || echo "  nvidia_modeset modprobe failed"
sudo modprobe nvidia_uvm 2>&1 || echo "  nvidia_uvm modprobe failed"

echo ""
echo "=== verify ==="
lsmod | grep -i nvidia | head -5
echo ""
nvidia-smi --query-gpu=name,memory.used,memory.free,memory.total --format=csv 2>&1 | head -3
echo ""

echo "=== restart ollama so it sees the GPU ==="
sudo systemctl restart ollama
sleep 4
echo ""

echo "=== test 14b gen (should be ~3s with GPU) ==="
time curl -s --max-time 60 http://localhost:11434/api/generate -d '{"model":"qwen2.5-coder:14b","prompt":"say READY","stream":false,"options":{"num_ctx":16384}}' | jq -r '.response // .error // "EMPTY"'

echo ""
echo "=== KV buffer location (should say CUDA0 if GPU works) ==="
sudo journalctl -u ollama -n 30 --no-pager | grep -E "KV buffer|n-gpu-layers" | tail -5
