# marpogaus.run0_pipe

An Ansible become plugin that switches user with `run0 --pipe`.

`community.general.run0` allocates a terminal, and a terminal line discipline
corrupts a piped module, so that plugin sets `pipelining = False`: eight SSH
operations per task instead of one. `run0 --pipe` runs the command without a
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
   SSH user without authentication. `run0 --pipe` has no terminal to ask on;
   without the rule every task fails with `==== AUTHENTICATION FAILED ====`.
2. On an SELinux host, a policy module that lets `init_t` and
   `system_dbusd_t` use a `fifo_file` labelled `sshd_session_t`: `run0 --pipe`
   hands the SSH session's pipes to systemd as the unit's stdin and stdout.

Both are host configuration, not part of this collection. The
`run0_pipe_policy` role in
[ansible-base](https://github.com/MArpogaus/home-server-core) installs the
SELinux module; the polkit rule is placed by Ignition there.

## Options

`become_user`, `become_exe` and `become_flags`, with the usual variables
(`ansible_become_user`, ...) and the ini section `run0_pipe_become_plugin`.
