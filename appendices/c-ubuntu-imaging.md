# Appendix C — Pre-flight: Getting Ubuntu 24.04 onto the Workstations

**Audience: instructors / IT.** Do this **before workshop day** — Module 1
assumes students sit down at a fresh Ubuntu 24.04 login. Budget ~45 minutes
for the first machine, ~25 for each after (they can run in parallel with one
USB per machine, or serially with one).

Students deliberately do *not* do this step: OS installation is mostly
waiting at progress bars, and the workshop's limited GPU-hours are better
spent on drivers, serving, and code.

## Decisions to make once

- **Keep Windows?** The Precision 5860s (Kensington/Camden) have **two**
  2 TB NVMe drives — the clean option is Ubuntu on drive 1, Windows untouched
  on drive 0, choosing OS via the F12 boot menu. The Newark T2s have a single
  drive; either sacrifice Windows or shrink its partition first (from
  Windows: Disk Management → shrink C: by ≥300 GB).
- **Username:** use the same one on every box (suggested: `hopeworks`) so
  the module docs match every machine. Students share this account —
  workshop boxes, not personal machines.
- **Hostnames:** `llm-ws-01` … `llm-ws-05` (site-prefixed if you like:
  `ken-llm-01`). Label each physical box with hostname AND, on workshop day,
  its IP — Modules 2 and 4 need the IP constantly.

## 1. Make the install USB

On any machine, download **Ubuntu Desktop 24.04 LTS** from
<https://ubuntu.com/download/desktop> and write it to an 8 GB+ USB stick
with balenaEtcher (<https://etcher.balena.io/>) — fine here, since unlike the
UneeQ deployment kit there's no custom recovery partition involved.

> Ubuntu **Desktop**, not Server: students get a browser and GUI on the
> workstation — handy for Modules 1–3 (docs open next to the terminal).
> Everything in the workshop also works on Server if you prefer.

## 2. BIOS settings (per machine)

Power on, tap **F12** at the Dell logo → BIOS Setup:

1. **Secure Boot → Disabled.** Non-negotiable for this fleet: without a MOK
   (Machine Owner Key) enrollment, the NVIDIA kernel module won't load under
   Secure Boot — silently — and that's the single most common way to lose an
   hour on workshop day. MOK enrollment would keep Secure Boot on but adds
   an interactive boot step per machine; disabling is the consistent
   classroom choice.
2. SATA/NVMe operation: ensure **AHCI/NVMe** (not RAID-on) so the installer
   sees the drives.
3. Save, exit.

## 3. Install Ubuntu (per machine)

Boot with the USB inserted → F12 → pick the USB (UEFI entry):

1. **Try or Install Ubuntu** → Install.
2. Wired Ethernet connected (skip Wi-Fi setup entirely).
3. **Interactive installation**, default app selection.
4. **Do NOT check** "Install third-party software / graphics drivers" —
   Module 1 has students install the NVIDIA driver deliberately; pre-installing
   it would gut the lesson. (If you check it by accident, it's not fatal —
   `ubuntu-drivers install` in Module 1 becomes a no-op with the same verify steps.)
5. Disk: **5860s** → "Erase disk" targeting the *second* NVMe (verify by
   size/model!) or manual partitioning; **T2s** → erase disk (or install
   alongside Windows if you shrank it).
6. Account: name `hopeworks`, hostname per your scheme, a password students
   can type. Uncheck "require password to log in" nudges — keep the password.
7. Reboot, remove USB.

## 4. Post-install (per machine, ~10 min)

Log in and:

```bash
# Updates
sudo apt update && sudo apt upgrade -y

# SSH access (for your own remote admin of the fleet)
sudo apt install -y openssh-server
sudo systemctl enable --now ssh

# Confirm basics students will rely on
ip addr                 # note the wired IP; consider a DHCP reservation at the router
lspci | grep -i nvidia  # GPU visible
ping -c 2 archive.ubuntu.com   # DNS/network sane
```

**Ubuntu 24.04 gotchas** (learned the hard way on other Hopeworks
deployments):

- **DNS flakiness with systemd-resolved** is a known 24.04 issue. If name
  resolution misbehaves but `ping 1.1.1.1` works, the reliable bypass is a
  static `/etc/resolv.conf` (`echo "nameserver 1.1.1.1" | sudo tee /etc/resolv.conf`
  after disabling the symlink). The module troubleshooting tables mention the
  quick version for students.
- If you later enable SSH **password** auth and it doesn't take:
  `/etc/ssh/sshd_config.d/50-cloud-init.conf` overrides the main config —
  edit that file, then `sudo systemctl restart ssh`.

## 5. Pre-cache the models (strongly recommended)

The 7B model is ~15 GB; five machines pulling it simultaneously through one
uplink can eat 30–45 min of Module 2. The afternoon before, on **each**
machine, run Module 1 §4–5 yourself up through installing vLLM, then:

```bash
source ~/vllm-lab/.venv/bin/activate
hf download Qwen/Qwen2.5-7B-Instruct
```

Leave the **1.5B model NOT cached** — students should experience one real
download in Module 1, and 3 GB is quick. When students later run the 7B
download in Module 2, it verifies the cache and completes in seconds — the
run-book turns that into a teaching moment rather than a shortcut.

Doing this also proves end-to-end (driver path aside) that each box can
reach HuggingFace — surfacing any proxy/firewall surprise days early
instead of live.

## 6. Final state checklist (per machine)

- [ ] Boots to Ubuntu 24.04 login as `hopeworks`
- [ ] Wired Ethernet up; IP noted on the box's label
- [ ] `ping archive.ubuntu.com` resolves and responds
- [ ] Secure Boot disabled (`mokutil --sb-state` → "SecureBoot disabled")
- [ ] `lspci | grep -i nvidia` shows the GPU(s)
- [ ] SSH reachable from your machine
- [ ] Qwen2.5-7B in the HF cache (if pre-caching)
- [ ] **NVIDIA driver NOT installed** (`nvidia-smi` should fail — that's Module 1's job)
