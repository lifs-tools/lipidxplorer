[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.3483976.svg)](https://doi.org/10.5281/zenodo.3483976)
# LipidXplorer

LipidXplorer is a software that is designed to support bottom-up and top-down shotgun lipidomics experiments performed 
on all types of tandem mass spectrometers. Lipid identification does not rely on a database resource of reference 
or simulated mass spectra but uses user-defined molecular fragment queries. It supports accurate, isotope-corrected 
quantification based on the identified MS1 or MS2 level fragments.

## Downloading LipidXplorer

The latest (binary) release version of LipidXplorer is available from the [LIFS Portal](https://lifs-tools.org/lipidxplorer.html). 
You can obtain the source code for LipidXplorer from our [GitLab server](https://github.com/lifs-tools//lipidxplorer) and release version archives from [here](https://github.com/lifs-tools//lipidxplorer/-/releases).

## Running LipidXplorer on Windows

For Windows, we provide a single executable for LipidXplorer for download from the [LIFS Portal](https://lifs-tools.org/lipidxplorer.html).
Please download the zip-archive to a location of your choice and extract (unzip) the contents. 
Change to the unzipped LipidXplorer archive directory and simply double-click on `LipidXplorer.exe` to start it.

## Installation and Tutorials

Please see more detailed installation instructions on our [Wiki](https://lifs-tools.org/wiki/index.php/LipidXplorer_Installation).
These also cover the case of working with the source code.

[The Wiki](https://lifs-tools.org/wiki/index.php) also offers an overview of the concepts behind LipidXplorer, as well as tutorial and reference materials.

## Working with the LipidXplorer Source Code

LipidXplorer uses [uv](https://docs.astral.sh/uv/) to manage its Python
environment. Install uv, then from the project root:

    uv sync

This creates a `.venv` with the exact dependency versions recorded in
`uv.lock`, using the Python version pinned in `.python-version` (3.12).

Run the application with:

    uv run python LipidXplorer.py

Run the tests with:

    uv run pytest

On Linux, wxPython is installed from the wxPython project's own package
index, because no Linux wheel for it is published on PyPI. This is
configured in `pyproject.toml` and requires no manual steps, but it does
pin the Linux build to Ubuntu 24.04's GTK3 ABI. You will also need the GTK3
runtime libraries:

    sudo apt-get install libgtk-3-0 libglib2.0-0 libsm6 libxxf86vm1 \
                         libnotify4 libsdl2-2.0-0 libwebkit2gtk-4.1-0

### Alternative: conda environments

`uv` is the supported way to build and to reproduce a release, because
`uv.lock` is what CI resolves against. For people who would rather stay in
conda, two exported environments are kept in the project root and track the
same Python 3.12 / wxPython 4.2.2 combination:

    conda env create -f environment_windows.yml     # Windows
    conda env create -f environment_ubuntu.yml      # Linux
    conda activate lx15

There is no macOS environment file; use `uv` there. These files are exports,
not a lock file — they are refreshed by hand, so if they drift from
`uv.lock`, `uv.lock` is the authority.

## Building a Standalone Executable

The same command works on all three platforms:

    uv run pyinstaller --noconfirm LipidXplorer.spec

Output is `dist/LipidXplorer/` on Windows and Linux, and
`dist/LipidXplorer.app` on macOS.

PyInstaller cannot cross-compile: a Windows executable must be built on
Windows, a macOS app on macOS, and so on. Released binaries for all three
platforms are produced by the GitHub Actions workflow in
`.github/workflows/build.yml`.

### macOS

CI artifacts are signed ad-hoc by PyInstaller, which is not enough for
distribution: macOS quarantines anything downloaded through a browser, and
Gatekeeper rejects an app that carries no Developer ID and no notarization
ticket. Approving it under *System Settings > Privacy & Security* is not
reliable either — the bundle contains ~180 nested binaries, and the approval
does not consistently cover all of them, so the app dies while loading
libraries and no window ever appears.

To run an unsigned CI build locally, strip the quarantine flag:

```bash
find /path/to/LipidXplorer.app -exec xattr -d com.apple.quarantine {} \; 2>/dev/null
open /path/to/LipidXplorer.app
```

Note that `xattr -dr com.apple.quarantine` — the advice usually given — does
**not** work on macOS 26, which dropped the `-r` flag from `xattr`.

Releases should be signed and notarized instead; see below.

(On Linux, PyInstaller does not embed an application icon in the binary — it
prints a warning and skips that step, so the Linux binary has no embedded icon.)

### Signing and notarizing the macOS build (maintainers)

The whole flow is automated by `macos/sign-and-notarize.sh`; what follows is
the one-time setup it needs. It mirrors the LipidSpace script of the same name,
with the differences noted at the top of the file.

**1. Developer ID Application certificate.** In Xcode, go to *Settings >
Accounts*, select the team, *Manage Certificates… > + > Developer ID
Application*. Only the Account Holder may create these, and the number of them
is limited. Verify and note the team ID:

```bash
security find-identity -v -p codesigning
# 1) 864A249C...  "Developer ID Application: Nils Hoffmann (73367934A4)"
```

**2. Notarization credentials.** For local releases, create an app-specific
password at <https://appleid.apple.com> (*Sign-In and Security > App-Specific
Passwords*) and store it in the keychain once:

```bash
xcrun notarytool store-credentials "lipidxplorer-notary" \
  --apple-id "you@example.org" --team-id "73367934A4" --password "xxxx-xxxx-xxxx-xxxx"
```

**3. Build and release.**

```bash
uv sync
NOTARY_PROFILE=lipidxplorer-notary macos/sign-and-notarize.sh --build
```

This rebuilds the bundle, verifies nothing outside it is still linked, signs
every binary inside-out with the hardened runtime and a secure timestamp,
notarizes and staples the app, and writes
`dist/LipidXplorer-<version>-macos-<arch>.zip` and `.dmg`. The app is stapled
before the disk image is built, so the ticket travels with it when a user drags
it out of the DMG. Useful options: `--sign-only` (skip notarization),
`--no-dmg`, `--identity`, `--dist-name`, `--entitlements`; see
`macos/sign-and-notarize.sh --help`.

Run it once per architecture — a bundle built on Apple Silicon is arm64-only.

**Entitlements are not optional here.** `macos/entitlements.plist` grants three
things the hardened runtime otherwise blocks: `allow-jit` and
`allow-unsigned-executable-memory`, because numba compiles `@njit` functions at
runtime through llvmlite; and `disable-library-validation`, because CPython
`dlopen()`s ~180 extension modules from inside the bundle. Signing without them
produces an app that passes verification and then aborts the first time an MFQL
query reaches `lx/mfql/calcsf_cached.py`.

**Troubleshooting.** If notarization is rejected, the script prints the full
Apple log; the usual causes are a nested binary signed without the hardened
runtime or without a timestamp. `spctl -a -vvv -t exec dist/LipidXplorer.app`
reports `rejected / source=Unnotarized Developer ID` for an app that is signed
but not yet notarized — that is expected after `--sign-only`.

**4. Continuous delivery.** `.github/workflows/build.yml` signs and notarizes
the two macOS jobs when these repository secrets are present. Without them the
build still publishes a plain unsigned archive and logs a warning, so forks and
dry runs keep working.

| Secret | Contents |
| --- | --- |
| `MACOS_CERT_P12_BASE64` | `base64 -i certificate.p12` |
| `MACOS_CERT_PASSWORD` | password used when exporting the `.p12` |
| `ASC_KEY_P8_BASE64` | `base64 -i AuthKey_XXXX.p8` |
| `ASC_KEY_ID` | key ID of the App Store Connect API key |
| `ASC_ISSUER_ID` | issuer ID of the App Store Connect API key |

The App Store Connect API key (App Store Connect > *Users and Access >
Integrations > Keys*, role *Developer*) is preferred over an Apple ID password
in CI because it is scoped and does not expire when the password changes.
Export the `.p12` from Keychain Access with both the certificate **and** its
private key — losing the private key means burning another certificate slot.

Notarization round-trips through Apple and takes minutes, so CI signs only on
`v*` tags, or on a manual run of the workflow with **Sign and notarize the
macOS builds** ticked. Every other commit publishes the unsigned `.tar.gz`.
Use the manual run to prove the signing path works *before* you need it for a
release — otherwise its first execution is the one that matters.

Signed runs publish `.zip` and `.dmg` per architecture instead of the unsigned
`.tar.gz`; both are stapled, and the app is stapled before the disk image is
built so the ticket survives a drag out of the DMG.

## Versioning

We use [Semantic Versioning](http://semver.org/) for versioning of the software.
 
To browse available versions and releases, please see the [tags on this repository](https://github.com/lifs-tools//lipidxplorer/tags). 

## Authors

* **Ronny Herzog** - *Initial work*
* **Ballal Md. Hossen** - *Current Developer*
* **Jacobo Miranda Ackerman** - *Former Developer*
* **Lukas Müller** - *Contributor*
* **Fadi Al Machot** - *Contributor*
* **Nils Hoffmann** - *Contributor*

## License

This project is licensed under the GNU GPL License, version 2 - see the [COPYRIGHT.txt](COPYRIGHT.txt) file for details

## Help and Support

Please check our [Wiki](https://lifs-tools.org/wiki/index.php) on details on how to contact us to receive help and report errors.

## Citing the Software

Machine-readable citation metadata is in [CITATION.cff](CITATION.cff); GitHub's *Cite this repository* button renders it in APA and BibTeX.

Herzog R, Schwudke D, Shevchenko A: ***LipidXplorer: Software for Quantitative Shotgun Lipidomics Compatible with Multiple Mass Spectrometry Platforms***. **Current Protocols in Bioinformatics**, 15 October 2013, 43:14.12.1-14.12.30. [PUBMED](https://www.ncbi.nlm.nih.gov/pubmed/26270171) [DOI](https://doi.org/10.1002/0471250953.bi1412s43)
Herzog R, Schuhmann K, Schwudke D, Sampaio JL, Bornstein SR, Schroeder M, et al.: ***LipidXplorer: A Software for Consensual Cross-Platform Lipidomics***. **PLoS ONE**, 17 January 2012, 7(1):e29851. [PUBMED](https://pubmed.ncbi.nlm.nih.gov/22272252/) [DOI](https://doi.org/10.1371/journal.pone.0029851)
Herzog R, Schwudke D, Schuhmann K, Sampaio JL, Bornstein SR, Schroeder M, Shevchenko A: ***A novel informatics concept for high-throughput shotgun lipidomics based on the molecular fragmentation query language***. **Genome Biol.**, 19 January 2011, 12(1):R8. [PUBMED](https://pubmed.ncbi.nlm.nih.gov/21247462/) [DOI](https://doi.org/10.1186/gb-2011-12-1-r8)
