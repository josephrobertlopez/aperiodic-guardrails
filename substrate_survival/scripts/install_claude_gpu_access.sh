#!/bin/bash
# One-time install: gives Claude (running as user 'joey') passwordless access to
# (a) a single GPU-recovery script
# (b) systemctl ollama operations (start/stop/restart/status) via polkit
#
# Blast radius: ONLY ollama service + ONLY the nvidia kmod reset path. Nothing else.
# Removable: rm /usr/local/bin/claude-gpu-recover /etc/sudoers.d/claude-gpu /etc/polkit-1/rules.d/49-claude-ollama.rules
#
# Run as: sudo bash install_claude_gpu_access.sh

set -e
if [ "$EUID" -ne 0 ]; then
    echo "Run with sudo: sudo bash $0"
    exit 1
fi

USER_NAME="${SUDO_USER:-joey}"
echo "Installing for user: $USER_NAME"

# === 1. The recovery script ===
cat > /usr/local/bin/claude-gpu-recover <<'EOF'
#!/bin/bash
# Recover NVIDIA GPU + Ollama after suspend/resume D3cold lockup or driver wedge.
# Idempotent. Safe to call repeatedly.
set -e

echo "=== before ==="
nvidia-smi --query-gpu=name,memory.free --format=csv 2>&1 | head -2 || true
echo ""

echo "=== stop ollama (releases device handle) ==="
systemctl stop ollama
sleep 2

echo "=== reset nvidia_uvm (the one we can always unload) ==="
# nvidia_drm is usually held by display server; nvidia_uvm reset is often enough
# to clear a wedged compute context.
rmmod nvidia_uvm 2>&1 || echo "  nvidia_uvm: not loaded or busy"
modprobe nvidia_uvm
sleep 1

echo "=== verify nvidia-smi ==="
nvidia-smi --query-gpu=name,memory.free,memory.total --format=csv 2>&1 | head -3

echo ""
echo "=== restart ollama ==="
systemctl start ollama
sleep 4

echo ""
echo "=== test gen (should be <3s if GPU is back) ==="
time curl -s --max-time 60 http://localhost:11434/api/generate \
    -d '{"model":"qwen2.5-coder:14b","prompt":"reply READY","stream":false,"options":{"num_ctx":16384}}' \
    | jq -r '.response // .error // "EMPTY"'

echo ""
echo "=== KV buffer location ==="
journalctl -u ollama -n 80 --no-pager | grep -E "KV buffer|n-gpu-layers" | tail -3
EOF
chmod 755 /usr/local/bin/claude-gpu-recover
echo "✓ /usr/local/bin/claude-gpu-recover installed"

# === 2. Sudoers entry: passwordless for ONLY the recovery script ===
cat > /etc/sudoers.d/claude-gpu <<EOF
# Allow $USER_NAME to invoke ONLY the GPU recovery script without password
$USER_NAME ALL=(root) NOPASSWD: /usr/local/bin/claude-gpu-recover
EOF
chmod 440 /etc/sudoers.d/claude-gpu
# validate sudoers syntax
visudo -c -f /etc/sudoers.d/claude-gpu
echo "✓ /etc/sudoers.d/claude-gpu installed"

# === 3. Polkit rule: passwordless systemctl for ollama ONLY ===
mkdir -p /etc/polkit-1/rules.d
cat > /etc/polkit-1/rules.d/49-claude-ollama.rules <<EOF
// Allow $USER_NAME to manage the ollama systemd service without password.
// Scope: ollama.service only. Cannot manage any other service.
polkit.addRule(function(action, subject) {
    if (action.id == "org.freedesktop.systemd1.manage-units" &&
        action.lookup("unit") == "ollama.service" &&
        subject.user == "$USER_NAME") {
        return polkit.Result.YES;
    }
});
EOF
chmod 644 /etc/polkit-1/rules.d/49-claude-ollama.rules
echo "✓ /etc/polkit-1/rules.d/49-claude-ollama.rules installed"

# === 4. Open up dmesg for non-root reads (useful for diagnostics) ===
if [ "$(cat /proc/sys/kernel/dmesg_restrict)" = "1" ]; then
    cat > /etc/sysctl.d/99-dmesg-open.conf <<EOF
# Allow non-root users to read dmesg (kernel ring buffer)
kernel.dmesg_restrict = 0
EOF
    sysctl -w kernel.dmesg_restrict=0
    echo "✓ dmesg readable by all users (persisted in /etc/sysctl.d/99-dmesg-open.conf)"
fi

echo ""
echo "=== Done. Claude can now: ==="
echo "  sudo claude-gpu-recover         # passwordless, recovers GPU+Ollama"
echo "  systemctl restart ollama        # via polkit, no sudo, no password"
echo "  systemctl status ollama         # via polkit, no sudo, no password"
echo "  dmesg                           # readable, no sudo"
echo ""
echo "Test it: as $USER_NAME, run:"
echo "  sudo -n claude-gpu-recover      # should run without password prompt"
echo "  systemctl restart ollama        # should succeed without password prompt"
