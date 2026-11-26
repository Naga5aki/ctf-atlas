"""Acceptance contracts for the user-approved per-stack restoration page."""
from pathlib import Path
import hashlib, json, re, unittest
ROOT = Path(__file__).resolve().parents[1]
TEXT = (ROOT / "src/content-curation/forensic-website-reconstruction.md").read_text("utf-8")
PARTS = re.split(r"(?m)^## ", TEXT)[1:]
class SixStackAcceptanceTests(unittest.TestCase):
    def require(self, i, terms):
        self.assertEqual(len(PARTS), 6)
        for term in terms:
            self.assertIn(term, PARTS[i])
    def test_php_empty_www_returns_to_data_disk(self):
        self.require(0, ("lsblk -f", "/etc/fstab", "findmnt /www", "UUID", "不要因为", "空目录"))
    def test_php_configuration_and_rewrite_follow_framework(self):
        self.require(0, ("ThinkPHP", "Laravel", "WordPress", "database.php", ".env", "wp-config.php", "localhost", "套接字", "伪静态"))
    def test_java_profile_and_hosts_precede_jar_changes(self):
        self.require(1, ("spring.profiles.active", "SPRING_PROFILES_ACTIVE", "外部配置", "getent hosts", "容器 hosts", "不动 JAR"))
    def test_java_uses_original_tomcat_and_existing_dist(self):
        self.require(1, ("原 Tomcat", "CATALINA_BASE", "Context", "现成 `dist`", "只有源码"))
    def test_java_authentication_has_three_conditional_routes(self):
        self.require(1, ("###", "A．口令", "B．登录读取 Redis", "C．校验依赖外部服务", "该用户的 salt", "EX 120 NX", "TTL", "只调整一个 class"))
    def test_java_patch_preserves_account_scope_and_rollback(self):
        self.require(1, ("指定测试分支", "其他账号和错误输入", "恢复原 JAR", "修改后副本可操作", "原 JDK"))
    def test_mysql_plugin_compatibility_is_version_qualified(self):
        self.require(1, ("MySQL 8.4", "9.0", "默认禁用", "JDBC"))
    def test_python_environment_config_protocol_and_login(self):
        self.require(2, ("虚拟环境", "DJANGO_SETTINGS_MODULE", "DATABASES", "Flask", "uwsgi_pass", "PBKDF2", 'd["salt"]', 'd["iterations"]', "原校验函数"))
    def test_node_actual_environment_and_native_module_diagnosis(self):
        self.require(3, ("package.json", "NODE_ENV", "PM2", "systemd", "ABI", "--ignore-scripts", "实际加载", "会话"))
    def test_iis_binding_pool_effective_config_and_identity(self):
        self.require(4, ("绑定", "应用程序池", "processPath", "hostingModel", "Windows 集成认证", "sc-substatus", "500.19", "数据保护密钥"))
    def test_static_no_database_and_api_are_distinct(self):
        self.require(5, ("数据库＝无，已确认", "页面与接口", "静态 JSON", "不是数据库", "接口本身的类型", "PHP", "Java", "Python", "Node.js", "IIS"))
    def test_static_html_200_does_not_mask_missing_resources(self):
        self.require(5, ("内容是 HTML", "错误回退规则", "不是资源正常", "history", "刷新", "/api/"))
    def test_old_record_amount_status_acceptance_is_in_every_article(self):
        for i in range(6):
            self.require(i, ("旧", "编号", "金额", "状态", "三格回填"))
    def test_no_universal_password_or_competition_answer(self):
        for token in ("123456", "666666", "数证杯", "固定答案", "Replay-Only!2026"):
            self.assertNotIn(token, TEXT)
    def test_page_metadata_preserves_server_category_and_identifier(self):
        path = ROOT / "src/content/knowledge/forensic-website-reconstruction.md"
        header = path.read_text("utf-8").split("---", 2)[1]
        for token in ('module: "Forensics"', 'track: "服务器取证"', 'topic: "网站重构"', 'updated: "2026-10-14"'):
            self.assertIn(token, header)
    def test_server_category_has_six_direct_routes_to_existing_page(self):
        data = (ROOT / "src/data/forensics-taxonomy.ts").read_text("utf-8").split("export const websiteRecoveryRoutes = [", 1)[1]
        labels = re.findall(r"label: '([^']+)'", data)
        anchors = re.findall(r"anchor: '([^']+)'", data)
        self.assertEqual([s.split('：', 1)[0] for s in labels], ['PHP', 'Java', 'Python', 'Node.js', 'IIS', '静态站'])
        self.assertEqual(len(anchors), 6)
        for label in labels:
            self.assertIn(label, TEXT)
    def test_category_count_reports_workflows_not_invented_pages(self):
        page = (ROOT / "src/pages/module/[module].astro").read_text("utf-8")
        self.assertIn('websiteRecoveryRoutes.length} 类流程', page)
        self.assertIn('websiteRecoveryRoutes.map((route)', page)
        self.assertIn('/knowledge/${item.id}/#${route.anchor}', page)
        self.assertIn('knowledge.length', page)
    def test_current_review_record_marks_approved_structure_replacement(self):
        report = json.loads((ROOT / "docs/server-forensics-review-20261006.json").read_text("utf-8"))
        self.assertEqual(report["website_layout_20261014"]["stacks"], ["PHP", "Java", "Python", "Node.js", "IIS", "静态站"])
        self.assertTrue(report["website_layout_20261014"]["user_approved_replacement"])
        approved = report["approved_replacement_hashes_20261014"]
        self.assertIn("src/data/forensics-taxonomy.ts", approved)
        self.assertIn("src/pages/module/[module].astro", approved)
        for path, record in approved.items():
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), record["after"])
if __name__ == "__main__":
    unittest.main()
