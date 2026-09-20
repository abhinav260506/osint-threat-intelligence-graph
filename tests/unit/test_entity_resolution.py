"""Tests for Entity Resolution, Alias Mapping, and Entity Extraction."""

import pytest
from backend.app.normalization.entity_resolution import entity_resolver
from backend.app.extraction.entity_extractor import EntityExtractor


@pytest.fixture
def entity_extractor():
    return EntityExtractor()


class TestEntityResolution:
    """Validates canonical alias resolution across vendor naming schemes."""

    def test_resolves_apt29_by_canonical_name(self):
        entity, confidence = entity_resolver.resolve("APT29")
        assert entity is not None
        assert entity.canonical_name == "APT29"
        assert confidence == 1.0

    def test_resolves_cozy_bear_alias(self):
        entity, confidence = entity_resolver.resolve("Cozy Bear")
        assert entity is not None
        assert entity.canonical_name == "APT29"
        assert confidence >= 0.9

    def test_resolves_nobelium_alias(self):
        entity, confidence = entity_resolver.resolve("NOBELIUM")
        assert entity is not None
        assert entity.canonical_name == "APT29"

    def test_resolves_midnight_blizzard_alias(self):
        entity, confidence = entity_resolver.resolve("Midnight Blizzard")
        assert entity is not None
        assert entity.canonical_name == "APT29"

    def test_resolves_sandworm_aliases(self):
        for alias in ["Sandworm", "TeleBots", "Voodoo Bear", "Seashell Blizzard"]:
            entity, _ = entity_resolver.resolve(alias)
            assert entity is not None, f"Failed to resolve: {alias}"
            assert entity.canonical_name == "Sandworm"

    def test_resolves_lazarus_aliases(self):
        for alias in ["Lazarus Group", "HIDDEN COBRA", "Zinc", "APT38"]:
            entity, _ = entity_resolver.resolve(alias)
            assert entity is not None, f"Failed to resolve: {alias}"
            assert entity.canonical_name == "Lazarus Group"

    def test_resolves_volt_typhoon_aliases(self):
        for alias in ["Volt Typhoon", "Bronze Silhouette", "Vanguard Panda"]:
            entity, _ = entity_resolver.resolve(alias)
            assert entity is not None, f"Failed to resolve: {alias}"
            assert entity.canonical_name == "Volt Typhoon"

    def test_resolves_apt28_aliases(self):
        for alias in ["APT28", "Fancy Bear", "STRONTIUM", "Forest Blizzard"]:
            entity, _ = entity_resolver.resolve(alias)
            assert entity is not None, f"Failed to resolve: {alias}"
            assert entity.canonical_name == "APT28"

    def test_resolves_malware_families(self):
        for name in ["Cobalt Strike", "SUNBURST", "Mimikatz", "Industroyer", "AppleJeus"]:
            entity, _ = entity_resolver.resolve(name)
            assert entity is not None, f"Failed to resolve malware: {name}"

    def test_returns_none_for_unknown(self):
        entity, confidence = entity_resolver.resolve("CompleteFictionGroup999")
        assert entity is None
        assert confidence == 0.0

    def test_case_insensitive_resolution(self):
        entity, _ = entity_resolver.resolve("apt29")
        assert entity is not None
        assert entity.canonical_name == "APT29"


class TestEntityExtraction:
    """Validates extraction and classification from unstructured advisory text."""

    def test_extracts_known_threat_actors(self, entity_extractor):
        text = "APT29 (also known as Cozy Bear) deployed SUNBURST backdoors."
        entities = entity_extractor.extract_from_text(text)
        names = [e["canonical_name"] for e in entities]
        assert "APT29" in names

    def test_extracts_malware_families(self, entity_extractor):
        text = "The actor used Cobalt Strike beacons and Mimikatz for lateral movement."
        entities = entity_extractor.extract_from_text(text)
        names = [e["canonical_name"] for e in entities]
        assert "Cobalt Strike" in names
        assert "Mimikatz" in names

    def test_extracts_target_sectors(self, entity_extractor):
        text = "Targeted sectors include Government, Technology, and Financial Services."
        entities = entity_extractor.extract_from_text(text)
        sector_names = [e["canonical_name"] for e in entities if e["entity_type"] == "sector"]
        assert "Government" in sector_names
        assert "Technology" in sector_names
        assert "Financial Services" in sector_names

    def test_classifies_entity_types_correctly(self, entity_extractor):
        text = "Sandworm deployed Industroyer against Energy and Government targets."
        entities = entity_extractor.extract_from_text(text)
        type_map = {e["canonical_name"]: e["entity_type"] for e in entities}
        assert type_map.get("Sandworm") == "threat_actor"
        assert type_map.get("Industroyer") == "malware"
        assert type_map.get("Energy") == "sector"

    def test_extracts_dynamic_actor_designations(self, entity_extractor):
        text = "UNC3944 conducted social engineering attacks using phishing."
        entities = entity_extractor.extract_from_text(text)
        # UNC3944 should resolve to Scattered Spider
        names = [e["canonical_name"] for e in entities]
        assert any("UNC3944" in n or "Scattered Spider" in n for n in names)

    def test_deduplicates_entities(self, entity_extractor):
        text = "APT29 is also known as Cozy Bear. APT29 used SUNBURST."
        entities = entity_extractor.extract_from_text(text)
        apt29_entries = [e for e in entities if e["canonical_name"] == "APT29"]
        assert len(apt29_entries) == 1

    def test_provides_confidence_scores(self, entity_extractor):
        text = "Lazarus Group deployed AppleJeus."
        entities = entity_extractor.extract_from_text(text)
        for e in entities:
            assert "confidence" in e
            assert 0.0 < e["confidence"] <= 1.0

    def test_includes_country_attribution(self, entity_extractor):
        text = "APT28 (Russian GRU) targeted government networks."
        entities = entity_extractor.extract_from_text(text)
        apt28 = [e for e in entities if e["canonical_name"] == "APT28"]
        assert len(apt28) >= 1
        assert apt28[0]["country"] == "RU"
