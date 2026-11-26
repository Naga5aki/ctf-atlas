"""SSH editorial coverage, shell parsing and explicitly constructed fixtures.

These tests never invoke sshd, systemd, FinalShell or a forensic specimen.
"""
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
MAIN = "forensic-server-services"
TITLE = "## 14 SSH与远程访问取证"
SUBTITLES = (
    "SSH/OpenSSH基础", "sshd服务与进程", "SSH端口与网络", "sshd_config分析",
    "Linux账户与认证", "SSH Key取证", "SSH日志取证", "FinalShell连接排障",
    "SSH暴力破解分析", "SSH入侵分析", "SSH取证速查表",
)


def body(name):
    return (ROOT / "src/content-curation" / f"{name}.md").read_text("utf-8")


def section():
    text = body(MAIN)
    return text.split(TITLE, 1)[1].split("## 15 ", 1)[0] if TITLE in text else ""


def shell_blocks():
    return re.findall(r"(?ms)^```bash\n(.*?)^```", section())


def bash():
    return shutil.which("bash") or "C:/Program Files/Git/bin/bash.exe"


def posix(path):
    value = str(Path(path).resolve()).replace("\\", "/")
    return "/" + value[0].lower() + value[2:] if re.match(r"^[A-Za-z]:/", value) else value


class SSHServerContentTests(unittest.TestCase):
    def require(self, *phrases):
        value = section()
        self.assertTrue(value, "Expand the existing server-services section 14; do not add an article")
        for phrase in phrases:
            self.assertIn(phrase, value)
        return value

    def test_original_home_and_eleven_subsections_only(self):
        self.require()
        self.assertEqual(body(MAIN).count(TITLE), 1)
        self.assertEqual(re.findall(r"(?m)^### 14\.(\d+) (.+)$", section()),
                         [(str(i), title) for i, title in enumerate(SUBTITLES, 1)])
        self.assertEqual(re.findall(r"(?m)^## (\d\d) ", body(MAIN)), [f"{i:02}" for i in range(1, 16)])

    def test_server_only_hierarchy_and_navigation(self):
        self.require()
        linux = body("fic-case-03")
        self.assertIn("### 05.1 SSH与远程访问取证", linux)
        navigation = linux.split("### 05.1 SSH与远程访问取证", 1)[1].split("## 06 ", 1)[0]
        self.assertEqual(navigation.count("/knowledge/forensic-server-services/#14"), 12)
        self.assertIn("/knowledge/fic-case-03/#051-ssh与远程访问取证", body("forensic-guide-server"))
        self.assertNotIn("/knowledge/forensic-website-reconstruction", section())
        self.assertNotIn("/knowledge/forensic-remote-connections", section())

    def test_concepts_and_separate_authentication_domains(self):
        self.require("Secure Shell", "OpenSSH", "sshd", "FinalShell", "SSH/SFTP", "openssh-client",
                     "openssh-clients", "openssh-server", "Linux root ≠ MySQL root ≠ 宝塔账户 ≠ 网站后台账户", "NSS")

    def test_packages_and_mutating_operations_are_marked(self):
        text = self.require("dpkg -l | grep openssh", "rpm -qa | grep openssh", "sudo apt install openssh-server",
                            "sudo yum install openssh-server", "sudo dnf install openssh-server",
                            "【仅在副本/仿真/授权环境执行】", "仅有客户端")
        for block in shell_blocks():
            if re.search(r"(?:apt|yum|dnf) install|systemctl (?:start|restart|enable)|restart \"\$SSH_UNIT\"", block):
                before = text.split("```bash\n" + block, 1)[0].split("```", 1)[-1]
                self.assertIn("【仅在副本/仿真/授权环境执行】", before[-1400:])

    def test_services_daemons_and_socket_activation_are_distinct(self):
        self.require("systemctl status ssh", "systemctl status sshd", "ps -ef | grep '[s]shd'", "pgrep -a sshd",
                     "systemctl start ssh", "systemctl start sshd", "systemctl restart ssh", "systemctl restart sshd",
                     "systemctl enable ssh", "systemctl enable sshd", "ListenStream", "socket activation",
                     "不是查不到 sshd 就判定 SSH 不可用", "ExecStart", "MainPID", "DropInPaths")

    def test_ip_tcp_address_family_and_nonstandard_port(self):
        self.require("ip a", "hostname -I", "ip route", "Test-NetConnection", "TcpTestSucceeded",
                     "ping 不通 ≠ SSH 一定不通", "ping 通 ≠ SSH 一定可登录", "0.0.0.0:22", "[::]:22",
                     "127.0.0.1:22", "192.168.1.10:22", "27692", "IPv6", "NAT", "IP → 端口 → PID")

    def test_firewall_and_virtualization_are_in_the_network_section(self):
        self.require("sudo ufw status", "firewall-cmd --list-services", "firewall-cmd --list-ports",
                     "--get-active-zones", "--list-all-zones", "iptables -S", "nft list ruleset", "SELinux",
                     "Fail2ban", "TCP Wrappers", "6.7", "VMware", "VirtualBox", "Hyper-V", "Bridged",
                     "Host-only", "VMnet", "Connect at power on", "Connected")

    def test_all_configuration_fields_and_context_are_present(self):
        self.require("/etc/ssh/sshd_config.d/", "Include", "Match", "最先取得", "不是运行中进程", "-C user=analyst",
                     "-f", "-o", "-p", "KbdInteractiveAuthentication", "prohibit-password", "退出码为 0")
        for field in ("Port", "ListenAddress", "PermitRootLogin", "PasswordAuthentication", "PubkeyAuthentication",
                      "PermitEmptyPasswords", "AllowUsers", "DenyUsers", "AllowGroups", "DenyGroups",
                      "AuthenticationMethods", "MaxAuthTries", "UsePAM", "MaxStartups"):
            self.assertEqual(section().count(f"| `{field}` |"), 1, field)

    def test_accounts_keys_and_host_identity_evidence_boundaries(self):
        self.require("whoami", "getent passwd", "cat /etc/passwd", "/etc/shadow", "/etc/group", "Linux账户",
                     "/root/.ssh/", "/home/*/.ssh/", "authorized_keys", "known_hosts", "id_rsa", "id_ed25519",
                     "*.pub", "AuthorizedKeysFile", "from=", "command=", "restrict", "Host key verification failed",
                     "私钥属于高敏感证据", "不得用于登录其他系统", "不是成功登录清单")

    def test_logs_login_records_and_offline_paths_have_one_home(self):
        self.require("journalctl -u ssh -n 50 --no-pager", "journalctl -u sshd -n 50 --no-pager",
                     "tail -f /var/log/auth.log", "tail -f /var/log/secure", "Accepted password", "Accepted publickey",
                     "Failed password", "Invalid user", "Connection closed", "Disconnected from", "PAM",
                     "last -f ./work/var/log/wtmp", "lastb -f ./work/var/log/btmp", "lastlog", "源端口", "boot ID")
        original07 = body(MAIN).split("## 07 ", 1)[1].split("## 08 ", 1)[0]
        self.assertNotIn("last -f", original07)
        self.assertNotIn("rg -n 'Accepted|Failed password", original07)
        self.assertIn("#147-ssh日志取证", original07)

    def test_finalshell_chain_and_error_interpretation(self):
        self.require("标准排查顺序：网络 → 端口", "OpenSSH安装情况", "Linux账户存在", "建立SSH会话",
                     "Connection timed out", "Connection refused", "Permission denied", "Connection reset",
                     "主动 REJECT", "不直接忽略", "SFTP", "-o ExitOnForwardFailure=yes", "-L 127.0.0.1:18888")

    def test_bruteforce_is_not_equated_with_intrusion(self):
        self.require("一次 Failed password", "不能证明已入侵", "失败后成功", "PID复用", "账户变化",
                     "日志重复", "NAT", "时间线")
        flow = section().split("### 14.10 SSH入侵分析", 1)[1].split("### 14.11 ", 1)[0]
        self.assertEqual(re.findall(r"(?m)^(\d+)\. ", flow), [str(i) for i in range(1, 21)])
        for term in ("sudo", "Shell", "last / lastb / lastlog", "ps -ef", "ss -antp", "ss -lntp",
                     "crontab -l", "/etc/crontab", "/etc/cron.d/", "systemd", "WebShell"):
            self.assertIn(term, flow)

    def test_evidence_inventory_and_single_minute_table_are_not_new_articles(self):
        self.require("**SSH服务器取证 + FinalShell故障排查一分钟速查表**", "网络证据", "服务证据",
                     "配置证据", "账户证据", "密钥证据", "日志证据", "登录记录", "命令历史", "防火墙")
        self.assertEqual(section().count("**SSH服务器取证 + FinalShell故障排查一分钟速查表**"), 1)
        self.assertIn("#08-实战验证一项可疑定时任务", section())
        self.assertIn("#152-历史文件是线索计划任务按来源解释", section())
        self.assertNotIn("| `.ssh/known_hosts` |", body("fic-case-03"))

    def test_all_shell_examples_parse_without_execution(self):
        self.require()
        self.assertGreater(len(shell_blocks()), 14)
        for block in shell_blocks():
            result = subprocess.run([bash(), "-n"], input=block, capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_exact_port_filter_on_constructed_listener_text(self):
        self.require()
        line = next(line for block in shell_blocks() for line in block.splitlines() if line.startswith("ss -lntp | grep -E ':(22|27692)"))
        command = line.split("| ", 1)[1]
        data = "LISTEN 0 128 0.0.0.0:22 0.0.0.0:*\nLISTEN 0 128 [::]:27692 [::]:*\nLISTEN 0 128 127.0.0.1:2222 0.0.0.0:*\nLISTEN 0 128 [::]:276920 [::]:*\n"
        result = subprocess.run([bash(), "-c", "export PATH=/usr/bin:/bin:$PATH\n" + command], input=data, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), data.splitlines()[:2])

    def test_configuration_locator_reads_constructed_files_only(self):
        self.require()
        code = next(block for block in shell_blocks() if block.startswith("grep -Ei "))
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td)
            snippets = folder / "sshd_config.d"
            snippets.mkdir()
            main = folder / "sshd_config"
            main.write_text("# Port 22\nInclude /etc/ssh/sshd_config.d/*.conf\nPort 27692\nListenAddress 192.0.2.20\n", "utf-8")
            drop = snippets / "10-lab.conf"
            drop.write_text("Match User analyst\n  PasswordAuthentication no\n  PubkeyAuthentication yes\n", "utf-8")
            before = {p.name: p.read_bytes() for p in (main, drop)}
            code = code.replace("/etc/ssh/sshd_config.d/", f'"{posix(snippets)}/"').replace("/etc/ssh/sshd_config", f'"{posix(main)}"')
            result = subprocess.run([bash(), "-c", "export PATH=/usr/bin:/bin:$PATH\n" + code], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Port 27692", result.stdout)
            self.assertIn("Match User analyst", result.stdout)
            self.assertNotIn("# Port 22", result.stdout)
            self.assertEqual(before, {p.name: p.read_bytes() for p in (main, drop)})

    def test_log_locator_on_constructed_events_does_not_claim_compromise(self):
        self.require()
        command = next(block for block in shell_blocks() if block.startswith("# 已保全的未压缩日志"))
        rg = shutil.which("rg")
        self.assertIsNotNone(rg)
        # Use the documentation's exact pattern, a trusted rg, and only files we create.
        pattern = re.search(r"rg -n '([^']+)'", command)[1]
        messages = ("Accepted password", "Accepted publickey", "Failed password", "Invalid user",
                    "Connection closed", "Disconnected from", "session opened", "session closed", "sudo:", "pam_unix(sshd:auth)")
        with tempfile.TemporaryDirectory() as td:
            file = Path(td) / "constructed-auth.log"
            file.write_text("\n".join("LAB sshd[123]: " + item for item in messages) + "\nLAB unrelated message\n", "utf-8")
            before = file.read_bytes()
            result = subprocess.run([rg, "-n", pattern, str(file)], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(len(result.stdout.splitlines()), len(messages))
            self.assertNotIn("unrelated", result.stdout)
            self.assertEqual(before, file.read_bytes())

    def test_windows_client_examples_parse_but_do_not_send_network_requests(self):
        self.require()
        blocks = re.findall(r"(?ms)^```powershell\n(.*?)^```", section())
        self.assertEqual(len(blocks), 1)
        exe = shutil.which("pwsh") or shutil.which("powershell")
        if not exe:
            self.skipTest("PowerShell parser is not installed on this analysis host")
        with tempfile.TemporaryDirectory() as td:
            file = Path(td) / "client-example.ps1"
            file.write_text(blocks[0], "utf-8-sig")
            code = "$tokens=$null; $errors=$null; [System.Management.Automation.Language.Parser]::ParseFile($env:EXAMPLE_FILE,[ref]$tokens,[ref]$errors) | Out-Null; if ($errors.Count -ne 0) { $errors | Out-String | Write-Output; exit 1 }; Write-Output 'POWERSHELL_PARSE_OK network_requests=0'"
            result = subprocess.run([exe, "-NoProfile", "-NonInteractive", "-Command", code], env=dict(os.environ, EXAMPLE_FILE=str(file)), capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("POWERSHELL_PARSE_OK network_requests=0", result.stdout)

    def run_gate(self, status):
        self.require()
        code = next(block for block in shell_blocks() if block.startswith("# SSH replay syntax gate"))
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            trace = root / "trace.txt"
            daemon = root / "constructed-sshd"
            daemon.write_text('#!/usr/bin/env bash\nprintf "SSHD %s\\n" "$*" >> "$TRACE_FILE"\nif [[ $SYNTAX_RESULT != 0 ]]; then printf "CONSTRUCTED_CONFIG_ERROR\\n" >&2; fi\nexit "$SYNTAX_RESULT"\n', "utf-8", newline="\n")
            ctl = root / "constructed-systemctl"
            ctl.write_text('#!/usr/bin/env bash\nprintf "SYSTEMCTL %s\\n" "$*" >> "$TRACE_FILE"\nprintf "CONSTRUCTED_RESTART %s\\n" "$2"\n', "utf-8", newline="\n")
            daemon.chmod(0o755)
            ctl.chmod(0o755)
            env = dict(os.environ, SSHD_BIN=posix(daemon), SSHD_CONF="/work/replay/etc/ssh/sshd_config",
                       SYSTEMCTL_BIN=posix(ctl), SSH_UNIT="ssh.service", TRACE_FILE=posix(trace), SYNTAX_RESULT=str(status))
            result = subprocess.run([bash(), "-c", "export PATH=/usr/bin:/bin:$PATH\nsudo() { \"$@\"; }\n" + code],
                                    env=env, capture_output=True, text=True, encoding="utf-8")
            return result, trace.read_text("utf-8").splitlines()

    def test_failed_config_check_does_not_restart(self):
        result, calls = self.run_gate(255)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(calls, ["SSHD -t -f /work/replay/etc/ssh/sshd_config"])
        self.assertEqual(result.stderr, "CONSTRUCTED_CONFIG_ERROR\nSSH_CONFIG_INVALID\n")
        self.assertEqual(result.stdout, "")

    def test_successful_config_check_restarts_only_confirmed_unit(self):
        result, calls = self.run_gate(0)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls, ["SSHD -t -f /work/replay/etc/ssh/sshd_config", "SYSTEMCTL restart ssh.service"])
        self.assertEqual(result.stdout, "CONSTRUCTED_RESTART ssh.service\n")


if __name__ == "__main__":
    unittest.main()
