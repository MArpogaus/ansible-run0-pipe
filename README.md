# marpogaus.run0_pipe

An Ansible become plugin that switches user with `run0 --pipe`.

`community.general.run0` allocates a terminal. A terminal line discipline
corrupts a piped module, so that plugin sets `pipelining = False`. That costs
eight SSH operations per task instead of one. `run0 --pipe` runs the command without a
terminal, the module source travels on stdin, and pipelining works. On a
SecureBlue host a full deploy went from 413 s to 242 s.

The plugin is derived from `community.general.run0` and keeps its license,
GPL-3.0-or-later.

## Use

```yaml
# requirements.yml
collections:
  - name: https://github.com/MArpogaus/ansible-run0-pipe.git
    type: git
    version: main
```

```ini
# ansible.cfg
[privilege_escalation]
become = True
become_method = marpogaus.run0_pipe.run0_pipe
```

Two things on the host make it work:

1. A polkit rule that grants `org.freedesktop.systemd1.manage-units` to the
   SSH user without authentication. `run0 --pipe` has no terminal to ask on.
   Without the rule every task fails with `==== AUTHENTICATION FAILED ====`.
2. On an SELinux host, a policy module that lets `init_t` and
   `system_dbusd_t` use a `fifo_file` labelled `sshd_session_t`. `run0 --pipe`
   hands the SSH session's pipes to systemd as the unit's stdin and stdout.

Both are host configuration, not part of this collection. The
`run0_pipe_policy` role in
[home-server-core](https://github.com/MArpogaus/home-server-core) installs the
SELinux module. Ignition places the polkit rule there.

## Options

`become_user`, `become_exe` and `become_flags`, with the usual variables
(`ansible_become_user`, ...) and the ini section `run0_pipe_become_plugin`.

## Delta to upstream

This plugin adds `--pipe`, and sets `require_tty = False` and
`pipelining = True`. Three more things differ from `community.general.run0`.

`prompt` is empty here. Upstream waits for run0 to ask for a password. `--pipe`
gives the child no terminal, so polkit cannot ask and writes no prompt. A host
without the polkit rule fails instead.

`success` is a class attribute upstream, where it is dead. `BecomeBase`
assigns `self.success` on the instance, so the class value never takes part in
a comparison.

The colour-stripping helpers exist because a terminal makes run0 emit colour.
There is no terminal here, and `SYSTEMD_COLORS=0` covers the rest.

