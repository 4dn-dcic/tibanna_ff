#!/usr/bin/env bash
#
# Turn a fresh instance of the HMS IT RHEL 9 golden image into a Tibanna AMI builder.
#
# Runs on the builder instance as root. build-ami.sh sends it through SSM
# (AWS-RunShellScript) and snapshots the instance afterwards. Safe to run more than once.
#
# What gets installed mirrors tibanna/create_ami_userdata_rhel in the tibanna repo
# (the userdata used by `tibanna create_ami`). Keep the two in sync.
#
# Quirks of the golden image this works around:
#   - Its RHEL repos point at an internal mirror that a normal AWS subnet can't reach, so every
#     dnf transaction that touches them fails. Docker is therefore installed from Docker's repo
#     only, and the image is not updated here (IT ships it patched; that is the point of rebuilding).
#   - podman and container-selinux (Docker's main dependency) are preinstalled. The
#     podman-docker shim is removed so it can't shadow the real Docker CLI.
#
# Generalizing the image (machine-id, cloud-init state) is a separate step,
# generalize-instance.sh, run after verify-instance.sh.

set -euo pipefail

DOCKER_REPO_URL=https://download.docker.com/linux/centos/docker-ce.repo
DOCKER_REPO_FILE=/etc/yum.repos.d/docker-ce.repo
DOCKER_PACKAGES="docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin"
INSTANCE_USER=ec2-user
# Kernel modules the AWSF container needs from the host (it can't modprobe itself): netfilter and
# overlay for its nested dockerd (aws_run_workflow_generic.sh also loads these at runtime), and
# fuse for /dev/fuse, used by mount-s3 and fuse-overlayfs. Keep in sync with verify-instance.sh.
NESTED_DOCKER_MODULES="overlay br_netfilter ip_tables iptable_nat iptable_filter iptable_mangle fuse"
MODULES_FILE=/etc/modules-load.d/tibanna.conf

log() { echo "[configure] $*"; }
die() { echo "[configure] ERROR: $*" >&2; exit 1; }

[ "$(id -u)" -eq 0 ] || die "must run as root"
getent passwd "$INSTANCE_USER" >/dev/null || die "user $INSTANCE_USER does not exist on this image"

#######################################################################
#   1. Docker CE
#######################################################################
if rpm -q podman-docker >/dev/null 2>&1; then
    log "Removing podman-docker"
    dnf remove -y --disablerepo='*' podman-docker
fi

# Written with curl instead of 'dnf config-manager', which would refresh the unreachable repos
log "Adding Docker repo $DOCKER_REPO_URL"
curl -fsSL "$DOCKER_REPO_URL" -o "$DOCKER_REPO_FILE"

log "Installing $DOCKER_PACKAGES"
# shellcheck disable=SC2086
dnf install -y --disablerepo='*' --enablerepo='docker-ce-stable' $DOCKER_PACKAGES \
    || die "Docker install failed. If a dependency can't be resolved, it is missing from the image and only on the internal mirror"

# Started at boot, so it is up when the Tibanna userdata runs
systemctl enable --now docker
usermod -aG docker "$INSTANCE_USER"

# The Tibanna userdata installs its recurring jobs with crontab
systemctl enable --now crond 2>/dev/null \
    || echo "[configure] WARNING: crond can't be enabled (is cronie installed?)" >&2

#######################################################################
#   2. Kernel modules for the nested dockerd
#######################################################################
# Only modules that actually load go into the file: one that doesn't would leave
# systemd-modules-load.service failed on every boot.
log "Configuring kernel modules for nested docker"
loadable=""
for mod in $NESTED_DOCKER_MODULES; do
    if modprobe "$mod" 2>/dev/null; then
        loadable="$loadable $mod"
    else
        echo "[configure] WARNING: kernel module $mod does not load on this image" >&2
    fi
done
{
    echo "# Written by tibanna_ff scripts/smaht_ami/configure-instance.sh"
    echo "# Needed by the dockerd that runs inside the AWSF container"
    for mod in $loadable; do echo "$mod"; done
} > "$MODULES_FILE"
log "Modules loaded at boot:$loadable"

log "Done: $(docker --version)"
