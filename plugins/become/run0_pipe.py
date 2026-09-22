# Copyright (c) 2026, Marcel Arpogaus
# Derived from community.general.run0, GPL-3.0-or-later
# (https://www.gnu.org/licenses/gpl-3.0.txt); this file keeps that license.
from __future__ import annotations

DOCUMENTATION = """
name: run0_pipe
short_description: Switch user with run0, without a TTY
description:
  - Uses C(run0 --pipe), which runs the command without a terminal, so the
    module source can be fed on stdin and pipelining works.
  - The upstream C(community.general.run0) plugin allocates a TTY, and a
    terminal line discipline corrupts a piped module. It therefore sets
    C(pipelining = False), which costs eight SSH operations per task instead
    of one.
  - This plugin expects a polkit rule that grants the action without
    authentication. Without one, C(run0) has no way to ask and the task fails.
author: Marcel Arpogaus (@MArpogaus)
options:
  become_user:
    description: User to become.
    default: root
    ini:
      - section: privilege_escalation
        key: become_user
      - section: run0_pipe_become_plugin
        key: user
    vars:
      - name: ansible_become_user
      - name: ansible_run0_pipe_user
    env:
      - name: ANSIBLE_BECOME_USER
      - name: ANSIBLE_RUN0_PIPE_USER
    type: string
  become_exe:
    description: The run0 executable.
    default: run0
    ini:
      - section: privilege_escalation
        key: become_exe
      - section: run0_pipe_become_plugin
        key: executable
    vars:
      - name: ansible_become_exe
      - name: ansible_run0_pipe_exe
    env:
      - name: ANSIBLE_BECOME_EXE
      - name: ANSIBLE_RUN0_PIPE_EXE
    type: string
  become_flags:
    description: Options to pass to run0.
    default: ''
    ini:
      - section: privilege_escalation
        key: become_flags
      - section: run0_pipe_become_plugin
        key: flags
    vars:
      - name: ansible_become_flags
      - name: ansible_run0_pipe_flags
    env:
      - name: ANSIBLE_BECOME_FLAGS
      - name: ANSIBLE_RUN0_PIPE_FLAGS
    type: string
"""

from ansible.plugins.become import BecomeBase


class BecomeModule(BecomeBase):
    name = "run0_pipe"

    # The delta to community.general.run0 is three lines: --pipe below,
    # require_tty and pipelining. Everything upstream carries that is missing
    # here is missing on purpose, so that a reader does not restore it:
    #
    # - `prompt`: upstream expects run0 to ask for a password. --pipe gives the
    #   child no terminal, so polkit cannot ask and never writes a prompt. A
    #   host without the polkit rule fails instead, which is what the
    #   DOCUMENTATION above tells the operator to configure.
    # - `success`: upstream sets it as a class attribute, where it is dead.
    #   BecomeBase.__init__ assigns self.success = '' and then
    #   'BECOME-SUCCESS-%s' % self._id, so the instance attribute shadows the
    #   class one and upstream's marker is never compared against anything.
    # - the remove_ansi_codes helpers and the three check_* overrides: they
    #   exist because a TTY makes run0 emit colour. There is no TTY here, and
    #   SYSTEMD_COLORS=0 below covers the rest.
    prompt = ""
    fail = ("==== AUTHENTICATION FAILED ====",)
    require_tty = False
    pipelining = True

    def build_become_command(self, cmd, shell):
        super().build_become_command(cmd, shell)

        if not cmd:
            return cmd

        become = self.get_option("become_exe")
        flags = self.get_option("become_flags")
        user = self.get_option("become_user")

        return (
            f"SYSTEMD_COLORS=0 {become} --pipe --user={user} {flags} "
            f"{self._build_success_command(cmd, shell)}"
        )
