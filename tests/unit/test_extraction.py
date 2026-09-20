"""Tests for IoC Extraction, Defanging, and Validation."""

import pytest
from backend.app.extraction.ioc_extractor import IoCExtractor


@pytest.fixture
def extractor():
    return IoCExtractor()


class TestIoCExtraction:
    """Validates deterministic IoC extraction from unstructured text."""

    def test_extracts_defanged_ips(self, extractor):
        text = "The C2 server is located at 192[.]168[.]1[.]100 and fallback at 10.0.0.1"
        results = extractor.extract_from_text(text)
        ips = [r for r in results if r["ioc_type"] == "ipv4"]
        assert len(ips) >= 1
        normalized_values = [ip["normalized_value"] for ip in ips]
        assert "192.168.1.100" in normalized_values

    def test_extracts_defanged_domains(self, extractor):
        text = "Malicious domain: avsvmcloud[.]com and panprocess[.]com observed"
        results = extractor.extract_from_text(text)
        domains = [r for r in results if r["ioc_type"] == "domain"]
        domain_values = [d["normalized_value"] for d in domains]
        assert "avsvmcloud.com" in domain_values
        assert "panprocess.com" in domain_values

    def test_extracts_defanged_urls(self, extractor):
        text = "Payload was downloaded from hxxps://evil-server[.]com/malware/payload.exe"
        results = extractor.extract_from_text(text)
        urls = [r for r in results if r["ioc_type"] == "url"]
        assert len(urls) >= 1
        assert urls[0]["is_defanged"] is True

    def test_extracts_sha256_hashes(self, extractor):
        text = "Hash: 325ab288e119ba9a43f320b9a8784a8777923b5060da1d5e63539f1497bc4c7e"
        results = extractor.extract_from_text(text)
        hashes = [r for r in results if r["ioc_type"] == "sha256"]
        assert len(hashes) == 1
        assert hashes[0]["confidence"] == 1.0

    def test_extracts_cves(self, extractor):
        text = "The attacker exploited CVE-2020-10148 and CVE-2023-23397."
        results = extractor.extract_from_text(text)
        cves = [r for r in results if r["ioc_type"] == "cve"]
        cve_values = [c["normalized_value"] for c in cves]
        assert "CVE-2020-10148" in cve_values
        assert "CVE-2023-23397" in cve_values

    def test_extracts_attack_techniques(self, extractor):
        text = "Observed ATT&CK techniques: T1059, T1566, T1078, and T1195.002."
        results = extractor.extract_from_text(text)
        techniques = [r for r in results if r["ioc_type"] == "attack_technique"]
        tech_values = [t["normalized_value"] for t in techniques]
        assert "T1059" in tech_values
        assert "T1195.002" in tech_values

    def test_deduplicates_iocs(self, extractor):
        text = "IP: 54.193.127[.]211 was seen. Also 54.193.127[.]211 again."
        results = extractor.extract_from_text(text)
        ips = [r for r in results if r["ioc_type"] == "ipv4" and r["normalized_value"] == "54.193.127.211"]
        assert len(ips) == 1

    def test_includes_context_snippets(self, extractor):
        text = "The SUNBURST backdoor communicates with avsvmcloud[.]com for C2."
        results = extractor.extract_from_text(text)
        domains = [r for r in results if r["ioc_type"] == "domain"]
        assert len(domains) >= 1
        assert domains[0]["context_snippet"] != ""
