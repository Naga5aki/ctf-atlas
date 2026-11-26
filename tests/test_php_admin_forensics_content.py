"""Target-account recovery, salt and session contracts plus unchanged constructed lab behavior."""
from pathlib import Path
import importlib.util, re, subprocess, sys, unittest
ROOT = Path(__file__).resolve().parents[1]
def php():
    return (ROOT / "src/content-curation/forensic-website-reconstruction.md").read_text("utf-8").split("## 02 Java：", 1)[0]
class PHPAdminForensicsTests(unittest.TestCase):
    def run_lab(self, phase):
        result = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "public/practice/php_admin_evidence_lab.py"), phase], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()
    def test_php_has_six_steps_and_own_acceptance(self):
        self.assertEqual(re.findall(r"(?m)^### 01\.(\d+) ", php()), list("123456"))
        self.assertIn("## 01 PHP：恢复宝塔商城", php())
    def test_panel_and_website_accounts_are_separate(self):
        self.assertIn("面板账号不是商城后台账号", php())
        self.assertIn("会员登录与管理员登录", php())
    def test_own_salt_pepper_and_original_comparison_are_required(self):
        for token in ("自己的 `salt`", "全局密钥与用户 salt 是两回事", "实际口令比较语句", "原校验函数", "影响行数为 1"):
            self.assertIn(token, php())
    def test_hashing_is_not_decryption_or_web_error_disclosure(self):
        for token in ("不是解密", "不要通过网页错误提示输出摘要", "本地调试器", "原口令字段"):
            self.assertIn(token, php())
    def test_authentication_session_and_role_are_separate(self):
        for token in ("验证码", "账号禁用", "来源 IP", "会话存储", "Cookie", "角色权限"):
            self.assertIn(token, php())
    def test_historical_record_not_status_200_is_acceptance(self):
        self.assertIn("同一编号", php())
        self.assertIn("金额", php())
        self.assertIn("状态", php())
        self.assertIn("均不单独计为完成", php())
    def test_constructed_baseline_retains_original_password(self):
        self.assertEqual(self.run_lab("baseline"), "PHP_ADMIN_BASELINE login=False data_changed=False network_requests=0")
    def test_constructed_recovery_changes_only_selected_account(self):
        self.assertEqual(self.run_lab("modified"), "PHP_ADMIN_MODIFIED login=True wrong_password=False other_user_unchanged=True changed_rows=1 network_requests=0")
    def test_constructed_rollback_restores_behavior(self):
        self.assertEqual(self.run_lab("rollback"), "PHP_ADMIN_ROLLBACK original_digest_restored=True original_login=True replay_password=False network_requests=0")
    def test_constructed_negative_cases_are_unchanged(self):
        self.assertEqual(self.run_lab("self-test"), "PHP_ADMIN_SELFTEST checks=18 passed=18 network_requests=0")
if __name__ == "__main__":
    unittest.main()
