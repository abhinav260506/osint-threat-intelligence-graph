"""Curated Ground-Truth and OSINT Threat Intelligence Benchmark Corpora.

Contains realistic, documented public advisories for APT29, Sandworm, Lazarus,
Volt Typhoon, APT28, and candidate campaign variants to enable deterministic evaluation
of extraction, community detection, ML clustering, link prediction, and explainability.

Data is structured to produce meaningful graph overlaps:
  - APT29 reports share infrastructure (avsvmcloud.com, panprocess.com, 54.193.127.211)
  - Sandworm + APT28 share Russian-affiliated TTPs and sectors
  - Lazarus uses distinct DPRK infrastructure, but shares T1059 with others
  - Operation CloudStorm shares infrastructure with APT29 (intended discovery target)
  - Volt Typhoon uses living-off-the-land with overlapping Government targeting
"""

SAMPLE_CTI_REPORTS = [
    {
        "title": "CISA Alert AA20-352A: Advanced Persistent Threat Actor Compromises SolarWinds Supply Chain",
        "source_name": "CISA & FBI",
        "source_url": "https://www.cisa.gov/news-events/cybersecurity-advisories/aa20-352a",
        "source_tier": "TIER_1",
        "published_at": "2020-12-17T18:00:00Z",
        "content": """
        CISA and the FBI are tracking a significant cyber espionage campaign attributed to APT29 (also tracked as Cozy Bear, NOBELIUM, and The Dukes). 
        The threat actor inserted a malicious backdoor known as SUNBURST (Solorigate) into genuine SolarWinds Orion software builds.
        
        The SUNBURST backdoor communicates with command-and-control (C2) domains including avsvmcloud[.]com, freescanonline[.]com, and deftsecurity[.]com.
        Additionally, the actor used Cobalt Strike beacons and Mimikatz for lateral movement and credential theft.
        
        Observed Malicious Network Indicators:
        - 13.59.205[.]66
        - 54.193.127[.]211
        - hxxps://panprocess[.]com/api/v1/sync
        - hxxp://digitalcollege[.]org/updates/check
        
        Targeted Sectors:
        - Government
        - Technology
        - Defense
        - Financial Services
        
        MITRE ATT&CK Techniques:
        - T1059 (Command and Scripting Interpreter)
        - T1566 (Phishing)
        - T1078 (Valid Accounts)
        - T1003 (OS Credential Dumping)
        - T1195.002 (Supply Chain Compromise)
        
        Associated SHA-256 Hashes:
        - 325ab288e119ba9a43f320b9a8784a8777923b5060da1d5e63539f1497bc4c7e
        - d0d626deb3f9484e649703d183beec4d2b10e622792ff1f570e5e3930b612ac5
        
        Exploited CVEs:
        - CVE-2020-10148
        """,
    },
    {
        "title": "Mandiant M-Trends Report: Midnight Blizzard (APT29) Cloud Infiltration Tactics",
        "source_name": "Mandiant",
        "source_url": "https://www.mandiant.com/resources/blog/midnight-blizzard-cloud",
        "source_tier": "TIER_2",
        "published_at": "2023-03-15T12:00:00Z",
        "content": """
        Mandiant has observed advanced persistent threat group Cozy Bear (APT29, Midnight Blizzard) leveraging compromised OAuth applications.
        The threat actors abused Cobalt Strike and custom stealth loaders connecting to newly spun C2 domains:
        - panprocess[.]com
        - sync-azureupdate[.]com
        - 54.193.127[.]211
        - 89.44.9[.]237
        
        Targeted Sectors:
        - Government
        - Technology
        - Telecommunications
        
        Techniques Observed:
        - T1078 (Valid Accounts)
        - T1059 (Command and Scripting Interpreter)
        - T1003 (OS Credential Dumping)
        
        File Fingerprints:
        - a1b2c3d4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef0
        """,
    },
    {
        "title": "CISA Advisory: Sandworm Disrupts Ukrainian Energy Grid with Industroyer",
        "source_name": "CISA / CERT-UA",
        "source_url": "https://www.cisa.gov/news-events/cybersecurity-advisories/sandworm-industroyer",
        "source_tier": "TIER_1",
        "published_at": "2022-04-12T10:00:00Z",
        "content": """
        CERT-UA and international partners thwarted an attempt by Sandworm (TeleBots, Voodoo Bear, Russian GRU Unit 74455) to deploy Industroyer (Industroyer2) against high-voltage electrical substations.
        
        Sandworm attackers utilized living-off-the-land techniques, deploying C2 infrastructure across:
        - 194.28.172[.]71
        - 45.154.255[.]88
        - energy-grid-telemetry[.]net
        
        BlackEnergy was also deployed alongside Industroyer for persistent access to SCADA systems.
        
        Exploited Vulnerabilities:
        - CVE-2022-22954
        
        Targeted Sectors:
        - Energy
        - Critical Infrastructure
        - Government
        
        ATT&CK Techniques:
        - T1059 (Command and Scripting Interpreter)
        - T1485 (Data Destruction)
        - T1078 (Valid Accounts)
        
        SHA256 Hash:
        - 7c541571d87e1f40d6c9f6d6c8b9d8e7f6a5b4c3d2e1f0192837465019283746
        """,
    },
    {
        "title": "FBI Flash Advisory: Lazarus Group Cryptocurrency Theft and AppleJeus Campaign",
        "source_name": "FBI Cyber Division",
        "source_url": "https://www.fbi.gov/news/press-releases/lazarus-applejeus-flash",
        "source_tier": "TIER_1",
        "published_at": "2023-01-23T14:00:00Z",
        "content": """
        The FBI and CISA identify Lazarus Group (HIDDEN COBRA, Zinc) orchestrating widespread cryptocurrency targeting.
        The actors distributed weaponized trading applications masquerading as legitimate software via AppleJeus backdoors.
        
        C2 Endpoints:
        - crypto-trade-live[.]com
        - 185.193.125[.]14
        - hxxps://secure-wallet-api[.]org/v2/auth
        
        Targeted Sectors:
        - Financial Services
        - Technology
        
        ATT&CK Techniques:
        - T1566 (Phishing)
        - T1059 (Command and Scripting Interpreter)
        - T1082 (System Information Discovery)
        
        Hashes:
        - e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
        """,
    },
    {
        "title": "CISA Joint Advisory AA23-144A: Volt Typhoon Targets US Critical Infrastructure",
        "source_name": "CISA / NSA / FBI",
        "source_url": "https://www.cisa.gov/news-events/cybersecurity-advisories/aa23-144a",
        "source_tier": "TIER_1",
        "published_at": "2023-05-24T16:00:00Z",
        "content": """
        CISA, NSA, and the FBI have identified Volt Typhoon (also known as Bronze Silhouette and Vanguard Panda) 
        conducting cyber operations against US critical infrastructure organizations.
        
        The group uses living-off-the-land techniques and compromised SOHO routers for stealth proxy networks:
        - router-auth-update[.]com
        - 45.33.32[.]156
        - edge-proxy-telemetry[.]net
        
        Targeted Sectors:
        - Telecommunications
        - Energy
        - Government
        - Transportation
        
        ATT&CK Techniques:
        - T1078 (Valid Accounts)
        - T1059 (Command and Scripting Interpreter)
        - T1016 (System Network Configuration Discovery)
        - T1105 (Ingress Tool Transfer)
        
        Note: Unlike traditional Chinese APTs, Volt Typhoon avoids deploying custom malware 
        and instead abuses built-in operating system tools including wmic, netsh, and PowerShell.
        """,
    },
    {
        "title": "Mandiant Report: APT28 (Fancy Bear) Exploits Outlook Vulnerability in European Governments",
        "source_name": "Mandiant",
        "source_url": "https://www.mandiant.com/resources/blog/apt28-outlook-exploitation",
        "source_tier": "TIER_2",
        "published_at": "2023-06-14T10:00:00Z",
        "content": """
        Mandiant has observed APT28 (Fancy Bear, Sednit, STRONTIUM, Forest Blizzard) targeting European government 
        and military organizations through exploitation of Microsoft Outlook vulnerability.
        
        The group deployed Cobalt Strike beacons and leveraged Mimikatz for credential harvesting.
        
        Malicious Network Indicators:
        - mil-notify-center[.]com
        - 185.220.100[.]252
        - 91.215.85[.]147
        - hxxps://update-service-portal[.]com/auth/validate
        
        Exploited CVEs:
        - CVE-2023-23397
        - CVE-2023-38831
        
        Targeted Sectors:
        - Government
        - Defense
        - Aerospace
        
        ATT&CK Techniques:
        - T1566 (Phishing)
        - T1078 (Valid Accounts)
        - T1059 (Command and Scripting Interpreter)
        - T1003 (OS Credential Dumping)
        - T1110 (Brute Force)
        """,
    },
    {
        "title": "Candidate Investigation: Operation CloudStorm Targeting Critical Infrastructure",
        "source_name": "Cyber Threat Research Unit",
        "source_url": "https://threat-research.org/investigations/operation-cloudstorm",
        "source_tier": "TIER_3",
        "published_at": "2023-08-10T09:00:00Z",
        "content": """
        Security researchers have discovered an unclassified intrusion campaign dubbed Operation CloudStorm.
        The attackers were observed exploiting CVE-2020-10148 to penetrate high-profile targets.
        
        Forensic telemetry recovered malicious communication resolving to:
        - deftsecurity[.]com
        - 54.193.127[.]211
        - cloud-gateway-auth[.]com
        
        The tooling deployed shows heavy reuse of Cobalt Strike and Mimikatz.
        
        Targeted Sectors:
        - Government
        - Technology
        - Energy
        
        ATT&CK Techniques:
        - T1059 (Command and Scripting Interpreter)
        - T1003 (OS Credential Dumping)
        - T1078 (Valid Accounts)
        - T1195.002 (Supply Chain Compromise)
        
        Analyst Note: The overlap with APT29 SolarWinds infrastructure (deftsecurity.com, 54.193.127.211) 
        and identical TTP profile strongly suggests this campaign may be attributed to the same threat cluster.
        """,
    },
]
