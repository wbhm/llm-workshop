# Appendix D — Student Machine Setup (Dev Environment Prerequisites)

**Every student needs their own laptop or desktop, set up per this page,
before workshop day.** Modules 3 and 4 assume it — and setup on the day
burns class time that should go to building things. Everything here is a
free download; the whole page takes about 15–20 minutes.

Instructors: send this page to students ahead of the session, and verify
the machines aren't admin-locked against these installs (see the
[run-book](../instructor/run-book.md)).

## The machine itself

| Requirement | Details |
|---|---|
| OS | Windows 10/11, macOS 12+, or any recent Linux |
| Disk | ~2 GB free (tools only — no models ever land on your machine) |
| GPU | **Not needed.** Models run on the lab workstations; your machine is a client |
| Network | On the Hopeworks LAN (Wi-Fi or wired) with reach to the lab workstations |
| Permissions | Able to install software. **If your machine is Hopeworks-managed and an install is blocked, tell your instructor *before* workshop day** — not during it |

## Required installs

### 1. Python 3.10 or newer

Download from <https://www.python.org/downloads/>.

- **Windows:** in the installer, **check "Add python.exe to PATH"** — the
  single most important checkbox of this page.
- **macOS:** the python.org installer is fine; the command may be `python3`.

Verify:

```bash
python --version        # macOS: python3 --version
```

### 2. Git — and on Windows, Git Bash

- **Windows:** install **Git for Windows** from <https://gitforwindows.org/>
  (default options are fine). This provides two things the workshop needs:
  - **`git`** — to fetch the workshop code.
  - **Git Bash** — a bash terminal. **This is your required terminal for
    the whole workshop.** The workshop's commands are written for bash;
    their JSON quoting breaks in PowerShell and cmd.
- **macOS:** git comes with the developer tools — running `git --version`
  will offer to install them if missing. Your built-in Terminal is fine.
- **Linux:** `sudo apt install git` (or your distro's equivalent).

Verify:

```bash
git --version
```

### 3. Visual Studio Code

Download from <https://code.visualstudio.com/>. Then:

- Install the **Python** extension (Extensions sidebar → search "Python" →
  the one by Microsoft).
- **Windows:** set Git Bash as the default integrated terminal — Terminal
  menu → dropdown next to the `+` → **Select Default Profile** → **Git
  Bash**. Now every terminal you open inside VS Code is the right kind.

Any editor works in principle, but the modules' instructions assume VS Code.

### 4. A current browser

Chrome, Edge, or Firefox — whatever you have is almost certainly fine.

## Optional — advanced (React) track only

**Node.js 20+** from <https://nodejs.org/> (LTS version). Skip this unless
you're planning to do Module 4's React track. Verify: `node --version`.

## What you do NOT need

- A GPU, or a powerful machine — your code talks to the lab's GPUs over the network
- A HuggingFace account (only the optional [Appendix B](b-gated-models.md) homework uses one)
- Any paid account or subscription — everything in this workshop is free

## Final verification

Open a terminal (**Windows: Git Bash**) and run:

```bash
python --version      # 3.10 or newer  (macOS: python3 --version)
git --version         # any version
curl --version        # present on Windows 10+/macOS/Linux out of the box
```

Then open VS Code once so it finishes first-run setup.

**✅ Done when:** all three commands print versions, and VS Code opens with
the Python extension installed. The one check that must wait for workshop
day is network reach —
`curl http://<WORKSTATION_IP>:8000/v1/models` — done in Module 4 §1.
