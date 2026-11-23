#!/usr/bin/env bash
#
# Check that an instance has what the Tibanna runtime (awsf3/aws_run_workflow_generic.sh in the
# tibanna repo) needs from the AMI. Prints one OK/FAIL line per check and exits non-zero on any FAIL.
#
# Runs as root through SSM: build-ami.sh runs it on the builder after configuration, and again
# on a fresh instance launched from the new AMI (where Docker must come up on its own at boot).
# The last line is DOCKER_VERSION=<version>, which build-ami.sh puts in the AMI's tags.
# BOOT_TEST=1 (the instance launched from the new AMI) also checks that cloud-init ran the
# instance's userdata, which build-ami.sh sets to create USERDATA_MARKER.

set -u

BOOT_TEST=${BOOT_TEST:-0}
USERDATA_MARKER=/var/tmp/tibanna-userdata-ran
INSTANCE_USER=ec2-user
NESTED_DOCKER_MODULES="overlay br_netfilter ip_tables iptable_nat iptable_filter iptable_mangle fuse"

fail=0
ok()  { echo "OK   $*"; }
bad() { echo "FAIL $*"; fail=1; }

# Docker is started by systemd at boot and can still be coming up
docker_ready=0
for _ in $(seq 1 30); do
    docker info >/dev/null 2>&1 && { docker_ready=1; break; }
    sleep 2
done

rpm -q docker-ce >/dev/null 2>&1 && ok "docker-ce installed ($(rpm -q docker-ce))" || bad "docker-ce not installed"
rpm -q podman-docker >/dev/null 2>&1 && bad "podman-docker shim installed (would shadow the Docker CLI)" \
    || ok "no podman-docker shim"
docker_bin=$(command -v docker 2>/dev/null || true)
[ -n "$docker_bin" ] && rpm -qf "$docker_bin" 2>/dev/null | grep -q '^docker-ce-cli' \
    && ok "docker on PATH is Docker CE ($docker_bin)" || bad "docker on PATH ('$docker_bin') is not Docker CE"
systemctl is-enabled --quiet docker && ok "docker enabled at boot" || bad "docker not enabled at boot"
[ $docker_ready = 1 ] && ok "docker daemon answering" || bad "docker daemon not answering after 60s"

getent passwd "$INSTANCE_USER" >/dev/null && ok "user $INSTANCE_USER exists" || bad "user $INSTANCE_USER missing"
id -nG "$INSTANCE_USER" 2>/dev/null | grep -qw docker && ok "$INSTANCE_USER in group docker" \
    || bad "$INSTANCE_USER not in group docker"

for cmd in aws curl lsblk mkfs.ext4 modprobe python3; do
    command -v "$cmd" >/dev/null 2>&1 && ok "$cmd present" || bad "$cmd missing (used by the Tibanna userdata)"
done

for mod in $NESTED_DOCKER_MODULES; do
    modprobe "$mod" 2>/dev/null && ok "kernel module $mod loads" || bad "kernel module $mod does not load"
done
[ -c /dev/fuse ] && ok "/dev/fuse present" || bad "/dev/fuse missing (mount-s3 and fuse-overlayfs need it)"

# The Tibanna userdata installs its recurring jobs (spot termination watch, ...) with crontab
command -v crontab >/dev/null 2>&1 && ok "crontab present" || bad "crontab missing (used by the Tibanna userdata)"
systemctl is-enabled --quiet crond 2>/dev/null && ok "crond enabled at boot" || bad "crond not enabled at boot"

# generalize-instance.sh deletes the host keys; sshd-keygen must recreate them at boot
if systemctl is-enabled --quiet sshd 2>/dev/null; then
    ls /etc/ssh/ssh_host_*_key >/dev/null 2>&1 && ok "SSH host keys present" || bad "sshd enabled but no SSH host keys"
fi

if [ "$BOOT_TEST" = 1 ]; then
    # Userdata runs late in boot and can still be running when SSM comes online
    for _ in $(seq 1 60); do
        [ -e "$USERDATA_MARKER" ] && break
        sleep 2
    done
    [ -e "$USERDATA_MARKER" ] && ok "cloud-init ran the userdata" \
        || bad "cloud-init did not run the userdata within 2 minutes (Tibanna starts every job through it)"
fi

token=$(curl -s -m 5 -X PUT http://169.254.169.254/latest/api/token \
    -H "X-aws-ec2-metadata-token-ttl-seconds: 60" || true)
[ -n "$token" ] && ok "IMDSv2 token" || bad "no IMDSv2 token"

echo "DOCKER_VERSION=$(docker version --format '{{.Server.Version}}' 2>/dev/null || echo unknown)"
exit $fail
