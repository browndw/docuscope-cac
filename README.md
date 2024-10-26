# *DocuScope Corpus Analysis & Concordancer Desktop* [![LICENSE][license-image]][license-url]

<div class="image" align="center">
    <img width="150" height="auto" src="https://raw.githubusercontent.com/browndw/docuscope-cac/main/js/app/icons/icon_256x256x32.png" alt="DocuScope logo">
    <br>
</div>

---

## Introduction

A desktop-application that processes and tags text for both parts-of-speech and rhetorical discourse features: 

-   the [online-version][online-version] is available for processesing small corpora (< 2 million word)
-   the desktop version enables the analysis of larger corpora

#### [Open Documentation][docs]

## Installation

### Application (Binaries)

Current version: v0.3.1.

[Download DocuScope CAC for Windows (.exe)][windows]

[Download DocuScope CAC for macOS (.dmg)][mac-intel]

### Build from Source

#### Prerequisites

Compiling a binary of DocuScope CAC has the following prerequisites:

* [poetry][poetry]: dependency management
* [Node.js][node-js]: JavaScript runtime
* [Yarn][yarn]: package manager

#### PyOxidizer

Install PyOxidizer by installing all the project build dependencies:

``` bash
$ poetry install -E build -E cli
```

Then run:

``` bash
$ poetry run docuscope dev build --install
```

The final built application for your current OS will be contained within `js/app/dist.`. 

### License

See [LICENSE][license-url].


[online-version]: https://docuscope-ca.eberly.cmu.edu/

[electron]: http://electron.atom.io/
[poetry]: https://python-poetry.org/docs/#installation
[yarn]: https://classic.yarnpkg.com/en/docs/install#debian-stable
[node-js]: https://nodejs.org/en/

[mac-intel]: https://github.com/browndw/docuscope-cac/releases/download/v0.3.2/DocuScope.CAC-0.3.2.dmg
[windows]: https://github.com/browndw/docuscope-cac/releases/download/v0.3.2/DocuScope.CAC.Setup.0.3.2.exe

[license-image]: https://img.shields.io/badge/license-Apache2-blue.svg
[license-url]: https://github.com/browndw/docuscope-cac/blob/main/LICENSE

[docs]: https://docuscope.github.io/
