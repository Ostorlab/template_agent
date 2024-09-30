# OXO Template Agent

This repo is a template for building an [OXO](https://github.com/ostorlab/ostorlab) agent in Python. It ships with
Good best practices like:

* Github actions workflow
* Linting checks with Ruff
* Static typing checks with Mypy
* Running the unit test with Pytest

## Getting Started

Here are links to good resources to get started:

* [Write your first Agent](https://oxo.ostorlab.co/tutorials/write_an_agent)
* [Use OXO to run scans](https://oxo.ostorlab.co/tutorials)
* [Debugging and Testing Agents](https://oxo.ostorlab.co/tutorials/debugging_agents)
* [Understand OXO Internals](https://oxo.ostorlab.co/tutorials/life_of_a_scan)

## Contributing

To contribute to this project, follow these steps:
1. Fork this repository.
2. Clone your forked repository: `git clone <your_fork_url>`
3. Navigate into your repository's directory: `cd <repository_directory>`
4. Create a new branch: `git checkout -b <branch_name>`.
5. Install the dependencies: `pip install -r requirements.txt`.
6. Make your changes.
7. Ensure the tests pass:
    ```sh
    pip install -r tests/test-requirements.txt
    pytest .
    ```
8. Ensure the linter passes:
    ```sh
    ruff format .
    ruff check .
    ```
9. Ensure the static type checks pass:
    ```sh
    pip install -r typing-requirements.txt
    mypy
    ```
10. Commit your changes: `git commit -m '<commit_message>'`.
11. Push to the remote branch: `git push origin <branch_name>`.
12. Create a pull request from the forked repository.


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
