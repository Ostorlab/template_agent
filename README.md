# Ostorlab Template Agent

This repo is a template for building an [Ostorlab](https://github.com/ostorlab/ostorlab) agent in Python. It ships with good best practices like:

* Github actions workflow
* Linting checks with Ruff
* Static typing checks with Mypy
* Running the unit test with Pytest

## Getting Started

Here are links to good resources to get started:

* [Write your first Agent](https://docs.ostorlab.co/tutorials/write-an-ostorlab-agent.html)
* [Use Ostorlab to run scans](https://docs.ostorlab.co/tutorials/run-your-first-scan.html)
* [Debugging and Testing Agents](https://docs.ostorlab.co/tutorials/debugging-agents.html)
* [Understand Ostorlab Internals](https://docs.ostorlab.co/tutorials/life-of-a-scan.html)

## Ideas for Agents to build

Implementation of popular tools like:

* ~~[semgrep](https://github.com/returntocorp/semgrep) for source code scanning.~~
* [nbtscan](http://www.unixwiz.net/tools/nbtscan.html): Scans for open NETBIOS nameservers on your target’s network.
* [onesixtyone](https://github.com/trailofbits/onesixtyone): Fast scanner to find publicly exposed SNMP services.
* [Retire.js](http://retirejs.github.io/retire.js/): Scanner detecting the use of JavaScript libraries with known
  vulnerabilities.
* [snallygaster](https://github.com/hannob/snallygaster): Finds file leaks and other security problems on HTTP servers.
* [testssl.sh](https://testssl.sh/): Identify various TLS/SSL weaknesses, including Heartbleed, CRIME and ROBOT.
* ~~[TruffleHog](https://github.com/trufflesecurity/truffleHog): Searches through git repositories for high entropy
  strings and secrets, digging deep into commit history.~~
* [cve-bin-tool](https://github.com/intel/cve-bin-tool): Scan binaries for vulnerable components.
* [XSStrike](https://github.com/s0md3v/XSStrike): XSS web vulnerability scanner with generative payload.
* ~~[Subjack](https://github.com/haccer/subjack): Subdomain takeover scanning tool.~~
* [DnsReaper](https://github.com/punk-security/dnsReaper): Subdomain takeover scanning tool.
