#!/usr/bin/env bash
#
# Remove per-instance state from the builder right before it is stopped and snapshotted,
# so it isn't cloned into every Tibanna instance launched from the AMI.
#
# Runs on the builder as root, sent through SSM by build-ami.sh as the last step on the
# instance. After this the builder should only be stopped, not used further.

set -euo pipefail

log() { echo "[generalize] $*"; }
[ "$(id -u)" -eq 0 ] || { echo "[generalize] ERROR: must run as root" >&2; exit 1; }

log "Cleaning dnf caches"
dnf clean all >/dev/null

# cloud-init then treats the next boot as a first boot, so it runs the Tibanna userdata
if command -v cloud-init >/dev/null 2>&1; then
    log "Resetting cloud-init state"
    cloud-init clean --logs
fi

# Otherwise every instance shares the builder's host keys. Deleted explicitly: cloud-init only
# does it if ssh_deletekeys is on. On RHEL 9 sshd-keygen@ recreates missing keys at boot
# (verify-instance.sh checks this on the boot test).
log "Removing SSH host keys"
rm -f /etc/ssh/ssh_host_*

# Empty machine-id: systemd generates a new one on the next boot
log "Resetting machine-id"
truncate -s 0 /etc/machine-id
rm -f /var/lib/dbus/machine-id

sync
log "Done"
