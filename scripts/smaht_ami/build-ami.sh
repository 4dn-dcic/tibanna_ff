#!/usr/bin/env bash
#
# Build a new SMaHT Tibanna AMI on the latest HMS IT RHEL golden image.
#
# Launches a throwaway builder from the golden image, installs Docker through SSM, verifies it,
# snapshots it into a new AMI, then boots a second throwaway instance from the new AMI and verifies
# again. Both instances are terminated. Nothing that exists already is changed or deleted, except
# that --activate then sets AMI_ID on the start_run Lambda (START_RUN_FUNCTION), the only setting
# Tibanna needs to launch the new AMI. Tibanna is never redeployed.
# See README.md in this folder for the one-time setup.
#
# Usage:
#   scripts/smaht_ami/build-ami.sh <config.env> [options]
#
#   --ami <id>       build from this golden AMI instead of the newest one matching GOLDEN_AMI_NAME_PREFIX
#   --name <name>    name of the new AMI (default: <AMI_NAME_PREFIX>-<golden image date>)
#   --keep-builder   if something fails, leave the builder / test instance running for debugging
#                    (Session Manager); terminate it by hand afterwards
#   --activate       after the new AMI passes its boot test, set AMI_ID=<new AMI> on the
#                    start_run Lambda (START_RUN_FUNCTION), so the next Tibanna runs use it.
#                    Skipped (exit 1) if Tibanna as deployed couldn't launch the AMI (root volume
#                    size or device, KMS key)
#   --yes            don't ask for confirmation

set -euo pipefail
# AWS CLI v2 pipes long output through a pager, which would stop an unattended build
export AWS_PAGER=""

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

usage() { sed -n '/^# Usage:/,/^$/p' "$0" | sed 's/^# \{0,1\}//'; exit 1; }
log() { echo "==> $*"; }
die() { echo "ERROR: $*" >&2; exit 1; }
need_value() { [ $# -ge 2 ] && [ -n "$2" ] || die "$1 needs a value"; }

#######################################################################
#   Arguments and config
#######################################################################
CONFIG=""; GOLDEN_ID=""; NEW_NAME=""; KEEP=0; ACTIVATE=0; YES=0
while [ $# -gt 0 ]; do
    case "$1" in
        --ami) need_value "$@"; GOLDEN_ID=$2; shift 2 ;;
        --name) need_value "$@"; NEW_NAME=$2; shift 2 ;;
        --keep-builder) KEEP=1; shift ;;
        --activate) ACTIVATE=1; shift ;;
        --yes) YES=1; shift ;;
        -h|--help) usage ;;
        -*) die "unknown option $1" ;;
        *) [ -z "$CONFIG" ] || usage; CONFIG="$1"; shift ;;
    esac
done
[ -n "$CONFIG" ] || usage
[ -f "$CONFIG" ] || die "config file $CONFIG not found"

set -a
# shellcheck disable=SC1090
. "$CONFIG"
set +a

for var in AWS_REGION GOLDEN_AMI_NAME_PREFIX GOLDEN_AMI_OWNER SUBNET_ID SECURITY_GROUP_ID INSTANCE_PROFILE; do
    [ -n "${!var:-}" ] || die "$var is not set in $CONFIG"
done
INSTANCE_TYPE="${INSTANCE_TYPE:-c5a.large}"
AMI_NAME_PREFIX="${AMI_NAME_PREFIX:-tibanna-smaht-rhel9}"
# Root volume the deployed Tibanna requests: DEFAULT_ROOT_EBS_SIZE in tibanna_smaht/vars.py
TIBANNA_ROOT_EBS_SIZE="${TIBANNA_ROOT_EBS_SIZE:-15}"
[[ "$TIBANNA_ROOT_EBS_SIZE" =~ ^[0-9]+$ ]] || die "TIBANNA_ROOT_EBS_SIZE must be a number of GiB"
EXPECTED_AMI_KMS_KEY="${EXPECTED_AMI_KMS_KEY:-}"
START_RUN_FUNCTION="${START_RUN_FUNCTION:-}"
[ $ACTIVATE = 0 ] || [ -n "$START_RUN_FUNCTION" ] || die "--activate needs START_RUN_FUNCTION in $CONFIG"

for f in configure-instance.sh verify-instance.sh generalize-instance.sh; do
    [ -f "$SCRIPT_DIR/$f" ] || die "$SCRIPT_DIR/$f is missing"
done

AWS="aws --region $AWS_REGION"
for cmd in aws python3; do
    command -v "$cmd" >/dev/null 2>&1 || die "$cmd is required"
done

#######################################################################
#   Helpers
#######################################################################

# CLI waiters give up after about 10 minutes; allow up to 30
wait_instance() {
    local waiter=$1 instance_id=$2 i
    for i in 1 2 3; do
        $AWS ec2 wait "$waiter" --instance-ids "$instance_id" && return 0
    done
    return 1
}

# Wait until the instance reports Online in SSM
wait_for_ssm() {
    local instance_id=$1 status i
    log "Waiting for $instance_id to come online in SSM"
    for i in $(seq 1 60); do
        status=$($AWS ssm describe-instance-information \
            --filters "Key=InstanceIds,Values=$instance_id" \
            --query 'InstanceInformationList[0].PingStatus' --output text 2>/dev/null || true)
        [ "$status" = "Online" ] && return 0
        sleep 10
    done
    echo "ERROR: $instance_id did not come online in SSM within 10 minutes" >&2
    return 1
}

# Check that an EC2 call would be allowed, without making it
dry_run() {
    local out
    out=$("$@" --dry-run 2>&1) && return 0
    case "$out" in *DryRunOperation*) return 0 ;; esac
    die "this AWS call would fail, so nothing was created: ${*:4}
$out"
}

# Tag specifications (JSON) for the given resource types: Name, EXTRA_TAGS from the config,
# then the Key=Value pairs given here (these win).
# $1 = Name, $2 = comma-separated resource types, rest = Key=Value
tag_specs() {
    local name=$1 types=$2; shift 2
    python3 - "$name" "$types" ${EXTRA_TAGS[@]+"${EXTRA_TAGS[@]}"} "$@" <<'EOF'
import json, sys
name, types, pairs = sys.argv[1], sys.argv[2].split(","), sys.argv[3:]
tags = {"Name": name}
for kv in pairs:
    key, sep, value = kv.partition("=")
    if not sep or not key:
        sys.exit(f"ERROR: bad tag '{kv}', expected Key=Value (check EXTRA_TAGS)")
    tags[key] = value
tag_list = [{"Key": k, "Value": v} for k, v in tags.items()]
print(json.dumps([{"ResourceType": t, "Tags": tag_list} for t in types]))
EOF
}

# Run a script on the instance through SSM, print its output, return its status.
# $1 = instance id, $2 = script file, remaining args = VAR=value to export first
run_on_instance() {
    local instance_id=$1 script=$2; shift 2
    local params command_id status=Pending errors=0 i
    params=$(mktemp)
    python3 - "$script" "$@" > "$params" <<'EOF'
import json, shlex, sys
script, assignments = sys.argv[1], sys.argv[2:]
exports = [f"export {a.split('=', 1)[0]}={shlex.quote(a.split('=', 1)[1])}" for a in assignments]
with open(script) as f:
    body = f.read()
print(json.dumps({"commands": ["\n".join(exports + [body])], "executionTimeout": ["1800"]}))
EOF
    command_id=$($AWS ssm send-command --instance-ids "$instance_id" \
        --document-name AWS-RunShellScript --comment "tibanna ami build: $(basename "$script")" \
        --parameters "file://$params" --query Command.CommandId --output text) || command_id=""
    rm -f "$params"
    [ -n "$command_id" ] || { echo "ERROR: ssm send-command failed" >&2; return 1; }

    for i in $(seq 1 200); do
        sleep 10
        if status=$($AWS ssm get-command-invocation --command-id "$command_id" \
                --instance-id "$instance_id" --query Status --output text 2>/dev/null); then
            errors=0
        else
            # the invocation can take a moment to appear after send-command
            status=Pending; errors=$((errors + 1))
            [ "$errors" -lt 12 ] || { echo "ERROR: cannot read the result of SSM command $command_id" >&2; return 1; }
        fi
        case "$status" in
            Pending|InProgress|Delayed) continue ;;
            *) break ;;
        esac
    done
    $AWS ssm get-command-invocation --command-id "$command_id" --instance-id "$instance_id" \
        --query StandardOutputContent --output text
    $AWS ssm get-command-invocation --command-id "$command_id" --instance-id "$instance_id" \
        --query StandardErrorContent --output text >&2
    [ "$status" = "Success" ]
}

# Launch an instance from $1 named $2 with the builder settings, plus any further
# run-instances arguments; prints the instance id
launch() {
    local image=$1 name=$2; shift 2
    $AWS ec2 run-instances --image-id "$image" "${LAUNCH_ARGS[@]}" "$@" \
        --tag-specifications "$(tag_specs "$name" instance,volume "tibanna:ami-build=$NEW_NAME")" \
        --query 'Instances[0].InstanceId' --output text
}

# Read the start_run Lambda's environment and check that it can be rewritten safely: the API
# replaces all variables at once, so writing back an incomplete set (e.g. when the variables
# can't be decrypted) would delete the rest, S3_ENCRYPT_KEY included. The variables are never
# printed or passed on a command line.
# No arguments: prints "<AMI_ID or unset><TAB><TIBANNA_FF_VERSION>".
# $1 = AMI, $2 = file: writes {"Variables": ...} with AMI_ID=$1 to the file instead.
lambda_env() {
    local env
    env=$($AWS lambda get-function-configuration --function-name "$START_RUN_FUNCTION" \
        --query Environment --output json) || return 1
    printf '%s' "$env" | python3 -c '
import json, sys
env = json.load(sys.stdin) or {}
error = env.get("Error")
if error:
    sys.exit("ERROR: the Lambda environment cannot be read: %s %s"
             % (error.get("ErrorCode", ""), error.get("Message", "")))
variables = env.get("Variables") or {}
missing = [k for k in ("TIBANNA_FF_VERSION", "S3_ENCRYPT_KEY") if not variables.get(k)]
if missing:
    sys.exit("ERROR: the Lambda environment has no %s, so it is not a tibanna_ff start_run Lambda "
             "or not fully readable. Not touching it" % " or ".join(missing))
if len(sys.argv) > 1:
    variables["AMI_ID"] = sys.argv[1]
    with open(sys.argv[2], "w") as f:
        json.dump({"Variables": variables}, f)
else:
    print("%s\t%s" % (variables.get("AMI_ID") or "unset", variables["TIBANNA_FF_VERSION"]))' "$@"
}

# Set AMI_ID=$1 on the start_run Lambda, keeping all its other environment variables,
# and check that it took
ENV_FILE=""
set_lambda_ami() {
    local ami=$1 now
    ENV_FILE=$(mktemp)
    lambda_env "$ami" "$ENV_FILE" || return 1
    # The response echoes the variables: keep it off the terminal
    $AWS lambda update-function-configuration --function-name "$START_RUN_FUNCTION" \
        --environment "file://$ENV_FILE" --query LastUpdateStatus --output text >/dev/null || return 1
    rm -f "$ENV_FILE"; ENV_FILE=""
    $AWS lambda wait function-updated --function-name "$START_RUN_FUNCTION" || return 1
    now=$(lambda_env) || return 1
    now=${now%%$'\t'*}
    [ "$now" = "$ami" ] || { echo "ERROR: AMI_ID on $START_RUN_FUNCTION is $now after the update" >&2; return 1; }
}

# Reasons Tibanna as deployed can't launch the new AMI. Shown as warnings; with --activate
# any of them stops the script before the Lambda is changed.
PROBLEMS=""
add_problem() { PROBLEMS="${PROBLEMS}  - $*"$'\n'; }

# Instances this run launched; terminated on exit (on failure only without --keep-builder)
LAUNCHED=""
cleanup() {
    local rc=$?
    [ -z "$ENV_FILE" ] || rm -f "$ENV_FILE"
    [ -n "$LAUNCHED" ] || return 0
    if [ $rc -ne 0 ] && [ $KEEP = 1 ]; then
        echo "--keep-builder: left running:$LAUNCHED. Terminate by hand when done:" >&2
        echo "  $AWS ec2 terminate-instances --instance-ids$LAUNCHED" >&2
        return 0
    fi
    log "Terminating$LAUNCHED"
    # shellcheck disable=SC2086
    $AWS ec2 terminate-instances --instance-ids $LAUNCHED >/dev/null \
        || echo "WARNING: could not terminate$LAUNCHED; terminate by hand" >&2
}
trap cleanup EXIT

terminate_now() {
    $AWS ec2 terminate-instances --instance-ids "$1" >/dev/null \
        || { echo "WARNING: could not terminate $1; terminate by hand" >&2; return 0; }
    LAUNCHED=${LAUNCHED/ $1/}
}

#######################################################################
#   1. Preflight (nothing is created here)
#######################################################################
log "Preflight (read-only)"
ACCOUNT=$($AWS sts get-caller-identity --query Account --output text) || die "AWS credentials are not working"

# Any account can share an AMI with this one, unasked: only take images owned by IT
if [ -z "$GOLDEN_ID" ]; then
    GOLDEN_ID=$($AWS ec2 describe-images --owners "$GOLDEN_AMI_OWNER" --executable-users self \
        --filters "Name=name,Values=${GOLDEN_AMI_NAME_PREFIX}*" "Name=state,Values=available" \
                  "Name=architecture,Values=x86_64" \
        --query 'sort_by(Images,&CreationDate)[-1].ImageId' --output text) || die "could not list AMIs"
    [ -n "$GOLDEN_ID" ] && [ "$GOLDEN_ID" != "None" ] \
        || die "no x86_64 AMI named ${GOLDEN_AMI_NAME_PREFIX}* owned by $GOLDEN_AMI_OWNER is shared with this account"
fi
GOLDEN_JSON=$($AWS ec2 describe-images --image-ids "$GOLDEN_ID" --query 'Images[0]' --output json) \
    || die "AMI $GOLDEN_ID not found"
[ "$GOLDEN_JSON" != "null" ] || die "AMI $GOLDEN_ID not found or not shared with this account"
IFS=$'\t' read -r GOLDEN_STATE GOLDEN_CREATED GOLDEN_NAME GOLDEN_ARCH GOLDEN_OWNER GOLDEN_ROOT_DEVICE \
    GOLDEN_ROOT_SIZE < <(python3 -c '
import json, sys
i = json.loads(sys.argv[1])
root = next((b for b in i.get("BlockDeviceMappings", []) if b.get("DeviceName") == i.get("RootDeviceName")), {})
print("\t".join(str(x) for x in (i["State"], i["CreationDate"], i["Name"], i["Architecture"], i["OwnerId"],
                                  i.get("RootDeviceName", "?"), root.get("Ebs", {}).get("VolumeSize", "?"))))' \
    "$GOLDEN_JSON")
[ "$GOLDEN_OWNER" = "$GOLDEN_AMI_OWNER" ] \
    || die "AMI $GOLDEN_ID ($GOLDEN_NAME) is owned by $GOLDEN_OWNER, not GOLDEN_AMI_OWNER ($GOLDEN_AMI_OWNER)"
[ "$GOLDEN_STATE" = "available" ] || die "AMI $GOLDEN_ID is $GOLDEN_STATE, not available"
[ "$GOLDEN_ARCH" = "x86_64" ] || die "AMI $GOLDEN_ID is $GOLDEN_ARCH; SMaHT pipelines need x86_64"

# Name of the new AMI: AMI_NAME_PREFIX plus the golden image's date, taken from its name
# (e.g. <prefix>-2026-10-19), or its creation date if the name has none
GOLDEN_DATE=$(echo "$GOLDEN_NAME" | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}' | tail -1 || true)
[ -n "$GOLDEN_DATE" ] || GOLDEN_DATE=${GOLDEN_CREATED%%T*}
NEW_NAME="${NEW_NAME:-$AMI_NAME_PREFIX-$GOLDEN_DATE}"

EXISTING=$($AWS ec2 describe-images --owners self --filters "Name=name,Values=$NEW_NAME" \
    --query 'Images[0].[ImageId,State]' --output text) || die "could not list this account's AMIs"
[ "$EXISTING" = "None" ] || [ -z "$EXISTING" ] \
    || die "an AMI named $NEW_NAME already exists (${EXISTING//$'\t'/, }): this golden image was built already. Pass --name to build another"

# Tibanna maps the root volume as /dev/sda1 with root_ebs_size GiB (tibanna/ec2_utils.py), and EC2
# refuses a root volume smaller than the AMI's
if [ "$GOLDEN_ROOT_DEVICE" != /dev/sda1 ]; then
    add_problem "the root device is $GOLDEN_ROOT_DEVICE, not /dev/sda1: Tibanna's root_ebs_size would add a blank disk instead of sizing the root volume"
fi
if ! [[ "$GOLDEN_ROOT_SIZE" =~ ^[0-9]+$ ]]; then
    add_problem "the golden image's root volume size is unknown, so it can't be checked against TIBANNA_ROOT_EBS_SIZE"
elif [ "$GOLDEN_ROOT_SIZE" -gt "$TIBANNA_ROOT_EBS_SIZE" ]; then
    add_problem "the root volume is ${GOLDEN_ROOT_SIZE} GiB, more than the ${TIBANNA_ROOT_EBS_SIZE} GiB Tibanna requests (TIBANNA_ROOT_EBS_SIZE), so EC2 would refuse every launch. Deploy a large enough DEFAULT_ROOT_EBS_SIZE (tibanna_smaht/vars.py) first, then set TIBANNA_ROOT_EBS_SIZE to match"
fi

LAUNCH_ARGS=(
    --instance-type "$INSTANCE_TYPE"
    --iam-instance-profile "Name=$INSTANCE_PROFILE"
    --subnet-id "$SUBNET_ID" --security-group-ids "$SECURITY_GROUP_ID" --no-associate-public-ip-address
    --metadata-options HttpTokens=required,HttpEndpoint=enabled,HttpPutResponseHopLimit=2
)
# Validates EXTRA_TAGS too
INSTANCE_TAGS=$(tag_specs "$NEW_NAME-builder" instance,volume "tibanna:ami-build=$NEW_NAME") || exit 1

# Permission and parameter checks (--dry-run creates nothing)
log "Checking permissions (dry run)"
dry_run $AWS ec2 run-instances --image-id "$GOLDEN_ID" "${LAUNCH_ARGS[@]}" --tag-specifications "$INSTANCE_TAGS"
# Fails here, not after the build, if the function is missing or can't be read
if [ $ACTIVATE = 1 ]; then
    LAMBDA_STATE=$(lambda_env) || die "cannot read the configuration of Lambda $START_RUN_FUNCTION (see error above)"
    IFS=$'\t' read -r OLD_LAMBDA_AMI LAMBDA_VERSION <<< "$LAMBDA_STATE"
fi

#######################################################################
#   2. Confirm
#######################################################################
echo
echo "Account:          $ACCOUNT ($AWS_REGION)"
echo "Golden image:     $GOLDEN_NAME ($GOLDEN_ID), owner $GOLDEN_OWNER"
echo "                  root $GOLDEN_ROOT_DEVICE, ${GOLDEN_ROOT_SIZE} GiB (Tibanna requests ${TIBANNA_ROOT_EBS_SIZE} GiB)"
echo "New AMI:          $NEW_NAME"
echo "Subnet / SG:      $SUBNET_ID / $SECURITY_GROUP_ID"
echo "Profile / type:   $INSTANCE_PROFILE / $INSTANCE_TYPE"
echo "Extra tags:       ${EXTRA_TAGS[*]:-none}"
[ $ACTIVATE = 0 ] || echo "start_run AMI_ID: $OLD_LAMBDA_AMI -> <new AMI>  ($START_RUN_FUNCTION, tibanna_ff $LAMBDA_VERSION)"
echo
echo "What happens (about 30-60 minutes):"
echo "  - a builder instance is launched from $GOLDEN_ID, Docker is installed and verified (SSM)"
echo "  - the builder is stopped and imaged into $NEW_NAME"
echo "  - a test instance is launched from $NEW_NAME and verified"
echo "  - both instances are terminated$([ $KEEP = 1 ] && echo " (kept if something fails: --keep-builder)")"
if [ $ACTIVATE = 1 ]; then
    echo "  - AMI_ID on Lambda $START_RUN_FUNCTION is set to the new AMI: the next Tibanna runs use it"
    echo "  Nothing else existing is changed; Tibanna is not redeployed."
else
    echo "  Nothing existing is changed; Tibanna keeps using its current AMI (no --activate)."
fi
if [ -n "$PROBLEMS" ]; then
    echo
    echo "WARNING: Tibanna as deployed could not launch the new AMI:"
    printf '%s' "$PROBLEMS"
    [ $ACTIVATE = 0 ] || echo "The AMI is still built and tested, but --activate will NOT change the Lambda."
fi
echo
if [ $YES = 0 ]; then
    while true; do
        read -r -p "Continue? [y/n]: " yn
        case $yn in
            [Yy]*) break ;;
            [Nn]*) exit 1 ;;
            *) echo "Please answer yes or no." ;;
        esac
    done
fi

#######################################################################
#   3. Builder: launch, configure, verify, generalize
#######################################################################
BUILDER=$(launch "$GOLDEN_ID" "$NEW_NAME-builder") || die "could not launch the builder"
LAUNCHED="$LAUNCHED $BUILDER"
log "Launched builder $BUILDER"
wait_instance instance-status-ok "$BUILDER" || die "builder $BUILDER did not pass its status checks"
wait_for_ssm "$BUILDER" || die "no SSM connection to the builder (the subnet needs a route to SSM without a public IP)"

log "Configuring $BUILDER"
run_on_instance "$BUILDER" "$SCRIPT_DIR/configure-instance.sh" || die "configuration FAILED (see output above)"

log "Verifying $BUILDER"
VERIFY_OUT=$(mktemp)
run_on_instance "$BUILDER" "$SCRIPT_DIR/verify-instance.sh" | tee "$VERIFY_OUT" \
    || { rm -f "$VERIFY_OUT"; die "verification of the builder FAILED (see output above)"; }
DOCKER_VERSION=$(sed -n 's/^DOCKER_VERSION=//p' "$VERIFY_OUT" | tail -1)
rm -f "$VERIFY_OUT"

log "Generalizing $BUILDER"
run_on_instance "$BUILDER" "$SCRIPT_DIR/generalize-instance.sh" || die "generalization FAILED (see output above)"

#######################################################################
#   4. Image
#######################################################################
log "Stopping $BUILDER"
$AWS ec2 stop-instances --instance-ids "$BUILDER" >/dev/null || die "could not stop $BUILDER"
wait_instance instance-stopped "$BUILDER" || die "$BUILDER did not stop"

log "Creating AMI $NEW_NAME"
IMAGE_TAGS=$(tag_specs "$NEW_NAME" image,snapshot "tibanna:ami-build=$NEW_NAME" \
    "tibanna:golden-ami-id=$GOLDEN_ID" "tibanna:golden-ami-name=$GOLDEN_NAME" \
    "tibanna:built=$(date +%Y-%m-%d)" "tibanna:docker-version=${DOCKER_VERSION:-unknown}")
NEW_AMI=$($AWS ec2 create-image --instance-id "$BUILDER" --name "$NEW_NAME" \
    --description "SMaHT Tibanna AMI: $GOLDEN_NAME + Docker ${DOCKER_VERSION:-}" \
    --tag-specifications "$IMAGE_TAGS" --query ImageId --output text) || die "create-image FAILED"
log "Waiting for $NEW_AMI to become available (can take 10-30 minutes)"
for i in $(seq 1 6); do
    $AWS ec2 wait image-available --image-ids "$NEW_AMI" 2>/dev/null && break
    state=$($AWS ec2 describe-images --image-ids "$NEW_AMI" --query 'Images[0].State' --output text || true)
    [ "$state" != "failed" ] || die "AMI $NEW_AMI failed to build"
    [ "$i" -lt 6 ] || die "AMI $NEW_AMI is still $state after an hour. Check it in the console; don't use it until it is available"
done
terminate_now "$BUILDER"

read -r SNAPSHOT_ID SNAPSHOT_KMS < <($AWS ec2 describe-snapshots --snapshot-ids "$($AWS ec2 describe-images \
    --image-ids "$NEW_AMI" --query 'Images[0].BlockDeviceMappings[0].Ebs.SnapshotId' --output text)" \
    --query 'Snapshots[0].[SnapshotId,KmsKeyId]' --output text) || { SNAPSHOT_ID="?"; SNAPSHOT_KMS="?"; }
DISCARD="$AWS ec2 deregister-image --image-id $NEW_AMI && $AWS ec2 delete-snapshot --snapshot-id $SNAPSHOT_ID"
if [ -n "$EXPECTED_AMI_KMS_KEY" ] && [ "$SNAPSHOT_KMS" != "$EXPECTED_AMI_KMS_KEY" ] \
        && [ "${SNAPSHOT_KMS##*/}" != "$EXPECTED_AMI_KMS_KEY" ]; then
    add_problem "the snapshot's KMS key ($SNAPSHOT_KMS) is not EXPECTED_AMI_KMS_KEY ($EXPECTED_AMI_KMS_KEY): Tibanna's run_task role can only launch it once AMI_KMS_KEY_ID names that key (a deploy_tiger, see the README)"
fi

#######################################################################
#   5. Boot test: Docker must come up on its own from the new AMI, and
#      cloud-init must run userdata (Tibanna starts every job through it)
#######################################################################
TEST_INSTANCE=$(launch "$NEW_AMI" "$NEW_NAME-boot-test" \
        --user-data $'#!/bin/bash\ntouch /var/tmp/tibanna-userdata-ran\n') \
    || die "could not launch an instance from $NEW_AMI. Don't deploy it; discard with: $DISCARD"
LAUNCHED="$LAUNCHED $TEST_INSTANCE"
log "Launched boot test instance $TEST_INSTANCE"
wait_instance instance-status-ok "$TEST_INSTANCE" \
    || die "BOOT TEST FAILED: $TEST_INSTANCE did not pass its status checks. Don't deploy $NEW_AMI; discard with: $DISCARD"
wait_for_ssm "$TEST_INSTANCE" \
    || die "BOOT TEST FAILED: no SSM connection to $TEST_INSTANCE. Don't deploy $NEW_AMI; discard with: $DISCARD"
run_on_instance "$TEST_INSTANCE" "$SCRIPT_DIR/verify-instance.sh" BOOT_TEST=1 \
    || die "BOOT TEST FAILED (see output above). Don't deploy $NEW_AMI; discard with: $DISCARD"
terminate_now "$TEST_INSTANCE"

#######################################################################
#   6. Activate: point the start_run Lambda at the new AMI
#######################################################################
if [ $ACTIVATE = 1 ]; then
    if [ -n "$PROBLEMS" ]; then
        echo >&2
        echo "Tibanna as deployed could not launch $NEW_AMI:" >&2
        printf '%s' "$PROBLEMS" >&2
        die "NOT activated: $NEW_AMI ($NEW_NAME) is built and tested, but Lambda $START_RUN_FUNCTION was not changed. Fix the above, then set AMI_ID=$NEW_AMI on it by hand (Lambda console, Configuration > Environment variables). To discard the AMI instead: $DISCARD"
    fi
    log "Setting AMI_ID=$NEW_AMI on Lambda $START_RUN_FUNCTION"
    set_lambda_ami "$NEW_AMI" \
        || die "activation FAILED (see error above). $NEW_AMI is built and tested; set AMI_ID=$NEW_AMI on Lambda $START_RUN_FUNCTION by hand (Lambda console, Configuration > Environment variables)"
fi

#######################################################################
#   7. Report
#######################################################################
echo
log "PASS: $NEW_AMI ($NEW_NAME) built from $GOLDEN_NAME, Docker ${DOCKER_VERSION:-?}"
echo "Snapshot:  $SNAPSHOT_ID, encrypted with ${SNAPSHOT_KMS:-no KMS key}"
if [ $ACTIVATE = 1 ]; then
    echo "start_run: AMI_ID on $START_RUN_FUNCTION changed from $OLD_LAMBDA_AMI to $NEW_AMI"
fi
if [ -n "$PROBLEMS" ]; then
    echo
    echo "WARNING: Tibanna as deployed could not launch this AMI:"
    printf '%s' "$PROBLEMS"
fi
echo
if [ $ACTIVATE = 1 ]; then
    if [ "$OLD_LAMBDA_AMI" = "unset" ]; then
        echo "To roll back: remove AMI_ID from Lambda $START_RUN_FUNCTION (Lambda console, Configuration >"
        echo "Environment variables); start_run then uses AMI_PER_REGION from tibanna_ffcommon/vars.py."
    else
        echo "To roll back: set AMI_ID back to $OLD_LAMBDA_AMI on Lambda $START_RUN_FUNCTION"
        echo "(Lambda console, Configuration > Environment variables)."
    fi
else
    echo "Tibanna still uses its current AMI. To switch, set AMI_ID=$NEW_AMI on the start_run Lambda"
    echo "(Lambda console, Configuration > Environment variables), or use --activate next time."
    echo "To discard this AMI instead: $DISCARD"
fi
cat <<EOF

IMPORTANT for the next deploy_core / deploy_tiger: a deploy recreates the Lambdas with the
environment of the shell it runs in. Run it with AMI_ID=$NEW_AMI exported, or start_run silently
falls back to AMI_PER_REGION in tibanna_ffcommon/vars.py (worth updating at the next release).
Deploy from Linux with Python 3.11 (a deploy from macOS breaks pydantic_core in the Lambdas), and
prefer deploy_core: deploy_tiger recreates the IAM roles, which silently voids cross-account
bucket and KMS key policies that name them.
EOF
