---
name: github-ssh-diagnosis
description: Diagnose and fix GitHub SSH authentication issues — host keys, agent persistence, key selection
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [GitHub, SSH, Authentication, Troubleshooting]
    related_skills: [github-auth]
---

# GitHub SSH Diagnosis

Diagnose why SSH authentication to GitHub isn't working. Run these steps in order.

## Step 1: Check host key

```bash
ssh-keyscan github.com >> ~/.ssh/known_hosts 2>/dev/null
```

## Step 2: Identify available keys

```bash
ls -la ~/.ssh/*.pub 2>/dev/null
ssh-add -l 2>/dev/null || echo "agent empty"
```

## Step 3: Test each key directly

```bash
ssh -i ~/.ssh/<keyfile> -T git@github.com
```

If this succeeds → SSH config issue (fix below).
If this fails with "Permission denied" → key not registered on GitHub.

## Step 4: Fix SSH config for key persistence

If `-i` works but `ssh -T` doesn't, ssh-agent isn't persisting keys. Add to `~/.ssh/config`:

```
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/<keyfile>
    IdentitiesOnly yes
```

```bash
chmod 600 ~/.ssh/config
```

Then test: `ssh -T git@github.com`

## Step 5: Verify git remote works

```bash
git ls-remote git@github.com:<username>/<repo>.git
```

Empty output with exit 0 = repo exists but has no branches.
"Repository not found" = wrong username or repo name.

## Key insight: ssh-agent session isolation

ssh-agent keys do NOT persist across terminal sessions. The `-i` flag tests a specific key directly, bypassing the agent. If `-i` works but `ssh -T` doesn't without `-i`, the SSH config `IdentityFile` directive is the fix — it tells SSH which key to use without relying on the agent.

## Also: set git to use SSH globally

```bash
git config --global url."git@github.com:".insteadOf "https://github.com/"
```

This avoids HTTPS auth prompts for all repos.
