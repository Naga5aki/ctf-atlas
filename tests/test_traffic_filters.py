"""Keep the protocol filter handbook paired and usable as a lookup page."""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / "src/content/knowledge/forensic-traffic-filters.md"
CURATION = ROOT / "src/content-curation/forensic-traffic-filters.md"


class TrafficFilterHandbookTest(unittest.TestCase):
    def text(self):
        return KNOWLEDGE.read_text(encoding="utf-8")

    def test_curation_body_matches_rendered_page(self):
        rendered = self.text().split("---", 2)[2]
        self.assertEqual(CURATION.read_text(encoding="utf-8").strip(), rendered.strip())
        self.assertNotIn("\r", KNOWLEDGE.read_bytes().decode("utf-8"))
        self.assertNotIn("\r", CURATION.read_bytes().decode("utf-8"))

    def test_page_stays_in_network_traffic_topic(self):
        head = self.text().split("---", 2)[1]
        self.assertIn("title: Wireshark 过滤", head)
        self.assertIn("module: Forensics", head)
        self.assertIn("track: 网络取证", head)
        self.assertIn("topic: 流量与协议", head)
        self.assertIn("tags: [流量]", head)

    def test_protocol_lookup_filters_remain_copyable(self):
        body = self.text().split("---", 2)[2]
        for token in (
            "tcp.flags.syn == 1 && tcp.flags.ack == 0",
            "dhcp.option.dhcp == 5",
            "tls.handshake.extensions_server_name",
            "ftp.passive.port",
            "smb2.nt_status == 0xc000006d",
            "mysql.query",
            "usb.capdata",
            "kerberos.CNameString",
        ):
            self.assertIn(token, body)
        self.assertNotIn("注解", body)
        headings = re.findall(r"^## \d\d ", body, re.M)
        self.assertGreaterEqual(len(headings), 12)
        self.assertLessEqual(len(headings), 18)
