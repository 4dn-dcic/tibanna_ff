# SMaHT Tibanna AMI: automated rebuild

HMS IT requires SMaHT workflow instances to run on their current hardened RHEL 9 golden image. When IT publishes a new golden image, run one command to build a new Tibanna AMI on it and, with `--activate`, switch Tibanna over to it.

| File | Runs on | Purpose |
|---|---|---|
| `build-ami.sh` | your machine | Finds the newest golden image, builds and tests the new AMI, optionally points Tibanna at it |
| `configure-instance.sh` | the builder (through SSM) | Installs Docker CE, enables it and crond at boot, sets up kernel modules for the AWSF container (nested dockerd, FUSE) |
| `verify-instance.sh` | the builder and the boot-test instance (through SSM) | Checks everything the Tibanna userdata needs from the AMI (Docker, cron, kernel modules, `/dev/fuse`, ...) |
| `generalize-instance.sh` | the builder (through SSM) | Resets machine-id and cloud-init state and deletes the SSH host keys just before the snapshot |
| `config.example.env` | | Template for the per-account config |

> This folder is public. Keep account IDs and resource IDs out of committed files. Per-account configs (`*.env`) here are gitignored.

## How it works

1. **Preflight, read-only.** Picks the newest available x86_64 image named `GOLDEN_AMI_NAME_PREFIX*` that is shared with the account and owned by `GOLDEN_AMI_OWNER` (or the one given with `--ami`, which must have the same owner: any account can share an AMI with ours unasked). It checks that Tibanna as deployed could launch it: root device `/dev/sda1`, root volume no larger than `TIBANNA_ROOT_EBS_SIZE`. With `--activate` it also reads the start_run Lambda, so a wrong name or permission fails before the build. The new AMI is named `<AMI_NAME_PREFIX>-<golden image date>`, e.g. `tibanna-smaht-rhel9-2026-11-01`. If that AMI already exists, the script stops: that golden image has been built already. A dry run checks that the builder launch would be allowed.
2. **Builder.** Launches a throwaway instance from the golden image (no public IP), waits for SSM, then runs `configure-instance.sh`, `verify-instance.sh` and `generalize-instance.sh` on it and shows their output. Generalizing resets machine-id and cloud-init state and deletes the SSH host keys.
3. **Image.** Stops the builder and creates the AMI from it. The AMI and its snapshot are tagged with the golden image ID and name, the build date and the Docker version. The builder is terminated once the AMI is available. If the snapshot's KMS key isn't `EXPECTED_AMI_KMS_KEY` (when set), that is noted as a problem.
4. **Boot test.** Launches a second throwaway instance from the **new** AMI, with a small userdata script, and runs `verify-instance.sh` again. This checks that the image launches (it is KMS-encrypted), that Docker comes up on its own at boot, that cloud-init runs the userdata (Tibanna starts every job through it) and that the SSH host keys were recreated. The instance is terminated.
5. **Activate** (only with `--activate`). Sets `AMI_ID` to the new AMI on the start_run Lambda (`START_RUN_FUNCTION`), see [Switch Tibanna to the new AMI](#switch-tibanna-to-the-new-ami). If any check in steps 1 or 3 found that Tibanna as deployed couldn't launch the AMI, the Lambda is **not** changed and the script exits with an error (the AMI is kept).
6. **Report.** Prints the new AMI ID, the KMS key of its snapshot, and how to switch to the AMI or roll back. **Tibanna is never redeployed and no old AMI is deleted.**

If a step fails, the script stops and terminates the instances it launched (`--keep-builder` leaves them running for debugging through Session Manager). An AMI that was created but failed the boot test is left in place, with the command to discard it.

What is installed mirrors `tibanna/create_ami_userdata_rhel` in the [tibanna](https://github.com/4dn-dcic/tibanna) repo (used by `tibanna create_ami`). Keep the two in sync. As there, Docker comes from Docker's own repo only and the image isn't updated with `dnf`: the golden image's RHEL repos point at an internal mirror that a normal AWS subnet can't reach, and IT ships the image patched.

**The IT startup script is not run.** The golden image ships a script that IT runs on new instances (`/opt/srce/scripts/start-gsstools.sh`). Running it on the builder would bake whatever it registers into every Tibanna instance cloned from the AMI, so the AMI is the golden image plus Docker only. Ask IT whether Tibanna instances must run it themselves.

## One-time setup (per account)

### 1. Network and instance profile

The builder and boot-test instances get no public IP. Their subnet must reach SSM and `https://download.docker.com` through a NAT gateway or VPC endpoints. The subnet used for the Sentieon license server works. The security group needs outbound HTTPS only.

The instance profile needs SSM access only (`AmazonSSMManagedInstanceCore`).

### 2. Permissions for whoever runs the build

`ec2:DescribeImages`, `ec2:DescribeInstances`, `ec2:DescribeInstanceStatus`, `ec2:DescribeSnapshots`, `ec2:RunInstances`, `ec2:StopInstances`, `ec2:TerminateInstances`, `ec2:CreateImage`, `ec2:CreateTags`, `iam:PassRole` on the instance profile's role, `ssm:SendCommand`, `ssm:GetCommandInvocation`, `ssm:DescribeInstanceInformation`, for `--activate` also `lambda:GetFunctionConfiguration` and `lambda:UpdateFunctionConfiguration` on the start_run Lambda, and use of the golden image's KMS key (`kms:CreateGrant`, `kms:Decrypt`, `kms:DescribeKey`, `kms:GenerateDataKeyWithoutPlaintext`, `kms:ReEncrypt*`). If you can launch the golden image from the console, you have the KMS part.

### 3. Write the config

```bash
cp scripts/smaht_ami/config.example.env scripts/smaht_ami/<account>.env
```

Fill in the required values. `GOLDEN_AMI_OWNER` is IT's account that owns the golden images (the config has the command to look it up; check that it is IT's before using it). `TIBANNA_ROOT_EBS_SIZE` (default 15) is the root volume the **deployed** start_run requests, `DEFAULT_ROOT_EBS_SIZE` in `tibanna_smaht/vars.py`: keep the two in sync. Set `EXPECTED_AMI_KMS_KEY` to the key Tibanna is deployed with as `AMI_KMS_KEY_ID`, so the script warns (and `--activate` stops) if a new golden image uses a different key. Set `EXTRA_TAGS` if account policies require tags on instances, volumes or images. For `--activate`, set `START_RUN_FUNCTION` to the deployed start_run Lambda (`start_run_tiger[_<usergroup>][_<suffix>]`).

## Rebuild

Prerequisites: the AWS CLI, `python3`, and credentials for the account. Takes about 30 to 60 minutes.

```bash
scripts/smaht_ami/build-ami.sh scripts/smaht_ami/<account>.env --activate
```

| Option | Effect |
|---|---|
| `--ami <ami-id>` | Build from this golden image instead of the newest one |
| `--name <name>` | Name of the new AMI (e.g. to rebuild a golden image that was built already) |
| `--keep-builder` | If something fails, leave the builder / test instance running for debugging |
| `--activate` | After the boot test passes, set `AMI_ID` on the start_run Lambda so the next runs use the new AMI. Not done (exit 1) if Tibanna as deployed couldn't launch the AMI |
| `--yes` | Skip the confirmation prompt |

It ends with `PASS: ami-... (<name>) built from <golden image>`.

## Switch Tibanna to the new AMI

Tibanna picks the AMI in a single place: the `AMI_ID` environment variable of the deployed **start_run** Lambda. start_run copies it into the run's `config.ami_id`, which `run_task` uses to launch the instance, ahead of `AMI_PER_REGION` and of the `ami_per_region` that Foursight sends (an `ami_id` set explicitly in the input JSON still wins). The step function always calls the latest Lambda configuration, so changing that one variable takes effect from the next run; runs already in progress keep their instance. No redeploy is needed.

- **`--activate`** does this after the boot test passes. It keeps the Lambda's other variables as they are (they are never printed: they include `S3_ENCRYPT_KEY`), checks that the new value took, and prints the previous value. It refuses to write if the variables can't be read in full (an `Error` from Lambda, or no `TIBANNA_FF_VERSION` / `S3_ENCRYPT_KEY`), since the API replaces all of them at once. Test in the dev account (`smaht-wolf`) with a small workflow before switching production.
- **Without `--activate`**, or to switch to another existing AMI, or **to roll back**: in the Lambda console, open the start_run Lambda, Configuration > Environment variables, and set `AMI_ID` (or remove it, if it was unset before, to fall back to `AMI_PER_REGION`).

**The next deploy undoes it unless `AMI_ID` is exported.** `deploy_core` and `deploy_tiger` delete and recreate the Lambdas, with the environment of the shell they run in. Without `AMI_ID=<ami>` exported there, start_run silently falls back to `AMI_PER_REGION` in `tibanna_ffcommon/vars.py`. Update `AMI_PER_REGION` at the next release so the default is current too. For deploys in general: run them from Linux with Python 3.11 (a deploy from macOS breaks `pydantic_core` in the Lambdas), and prefer `deploy_core`, since `deploy_tiger` recreates the IAM roles, which silently voids bucket and KMS key policies in other accounts that name them.

**KMS key.** The new AMI's snapshot is encrypted with the same key as the golden image (IT's key). As long as IT keeps using that key, nothing changes. If the script reports that the key differs from `EXPECTED_AMI_KMS_KEY`, Tibanna's `run_task` role must be granted the new key: set `AMI_KMS_KEY_ID` and run `deploy_tiger` (see `docs/ami.rst` in the tibanna repo; `--activate` does not do this), then have accounts that grant Tibanna roles access re-save their policies. IT must also allow the account in the new key's policy.

**Root volume.** Tibanna launches instances with the root volume mapped as `/dev/sda1`, sized `root_ebs_size` (SMaHT default: `DEFAULT_ROOT_EBS_SIZE` = 15 GiB in `tibanna_smaht/vars.py`; deployments without it use tibanna's 10 GiB). EC2 refuses a root volume smaller than the AMI's, and with another root device name the mapping would add a blank disk instead. The script reports either case, and `--activate` then stops.

## When something goes wrong

| Situation | What to do |
|---|---|
| `an AMI named ... already exists` | This golden image has been built already. Use that AMI, or pass `--name` to build another one. |
| `no x86_64 AMI named ... owned by ... is shared with this account` | IT hasn't shared a golden image with this account, or `GOLDEN_AMI_NAME_PREFIX` / `GOLDEN_AMI_OWNER` is wrong. |
| `AMI ... is owned by ..., not GOLDEN_AMI_OWNER` | The image (or the one given with `--ami`) isn't IT's. Don't build from it unless you know where it comes from. |
| `this AWS call would fail, so nothing was created` | The dry run was refused. The message names the AWS error: usually a missing permission, `iam:PassRole`, or a tag policy (set `EXTRA_TAGS`). |
| `did not pass its status checks` right after launch | Often the KMS key: the instance is terminated at once with `Client.InvalidKMSKey.InvalidState`. Check the instance's state reason in the console. |
| `no SSM connection` | The subnet can't reach SSM without a public IP, or the instance profile lacks SSM access. |
| `configuration FAILED` | Read the output above it. `Docker install failed`: Docker's repo isn't reachable, or a dependency is only on IT's internal mirror (then build from a subnet that reaches it). Re-run with `--keep-builder` to look at the instance through Session Manager. |
| `verification ... FAILED` | The `FAIL` lines name what's missing. A missing tool (e.g. `aws`) or kernel module means the golden image changed; ask IT or add it to `configure-instance.sh` (and `create_ami_userdata_rhel`). |
| `BOOT TEST FAILED` | The AMI was created but doesn't work, and the Lambda was not changed. Don't use it. Discard it with the printed command, fix the cause and rebuild with `--name`, or delete the AMI first and rebuild. |
| `AMI ... failed to build` or still pending after an hour | Check the AMI in the console. The builder has been terminated. |
| `--activate needs START_RUN_FUNCTION` / `cannot read the configuration of Lambda ...` | Stops before anything is launched. Set `START_RUN_FUNCTION` to the exact name from the Lambda console, and check the `lambda:GetFunctionConfiguration` permission. `the Lambda environment cannot be read` or `has no TIBANNA_FF_VERSION`: the function isn't a tibanna_ff start_run, or its variables can't be decrypted (KMS). |
| `NOT activated` | The AMI is built and tested, but a listed problem (root volume size or device, KMS key) means Tibanna as deployed can't launch it. Fix that first (e.g. deploy a larger `DEFAULT_ROOT_EBS_SIZE`, then raise `TIBANNA_ROOT_EBS_SIZE`), then set `AMI_ID` in the console. |
| `cloud-init did not run the userdata` | Tibanna couldn't start any job on this AMI. Check IT's cloud-init settings on the image (`/etc/cloud/cloud.cfg*`) with `--keep-builder`. |
| `activation FAILED` | The AMI is built and tested; only the Lambda update failed (usually `lambda:UpdateFunctionConfiguration`). Set `AMI_ID` on the start_run Lambda by hand in the console. |
