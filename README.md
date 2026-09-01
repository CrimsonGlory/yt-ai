<!-- MANPAGE: BEGIN EXCLUDED SECTION -->
<div align="center">

[![YT-AI](https://raw.githubusercontent.com/CrimsonGlory/yt-ai/master/.github/banner.svg)](#readme)

[![Release version](https://img.shields.io/github/v/release/CrimsonGlory/yt-ai?color=brightgreen&label=Latest&style=for-the-badge)](#installation "Installation")
[![Python Version](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2FCrimsonGlory%2Fyt-ai%2Frefs%2Fheads%2Fmaster%2Fpyproject.toml&style=for-the-badge)](https://github.com/CrimsonGlory/yt-ai/blob/master/pyproject.toml "Python Version")
[![PyPI](https://img.shields.io/badge/-PyPI-blue.svg?logo=pypi&labelColor=555555&style=for-the-badge)](https://pypi.org/project/yt-ai "PyPI")
[![Discord](https://img.shields.io/badge/Discord-%235865F2.svg?&logo=discord&logoColor=white&style=for-the-badge)](https://discord.gg/H5MNcFW63r "Discord")
[![License: Unlicense](https://img.shields.io/badge/-Unlicense-red.svg?style=for-the-badge)](LICENSE "License")
[![Commits](https://img.shields.io/github/commit-activity/m/CrimsonGlory/yt-ai?label=commits&style=for-the-badge)](https://github.com/CrimsonGlory/yt-ai/commits "Commit History")

</div>
<!-- MANPAGE: END EXCLUDED SECTION -->

yt-ai is a feature-rich command-line audio/video downloader with support for [thousands of sites](supportedsites.md). The project is a fork of [yt-dlp](https://github.com/yt-dlp/yt-dlp).

<!-- MANPAGE: MOVE "USAGE AND OPTIONS" SECTION HERE -->

<!-- MANPAGE: BEGIN EXCLUDED SECTION -->
* [INSTALLATION](#installation)
    * [Detailed instructions](https://github.com/yt-dlp/yt-dlp/wiki/Installation)
    * [Release Files](#release-files)
    * [Update](#update)
    * [Dependencies](#dependencies)
    * [Compile](#compile)
* [USAGE AND OPTIONS](#usage-and-options)
    * [General Options](#general-options)
    * [Network Options](#network-options)
    * [Geo-restriction](#geo-restriction)
    * [Video Selection](#video-selection)
    * [Download Options](#download-options)
    * [Filesystem Options](#filesystem-options)
    * [Thumbnail Options](#thumbnail-options)
    * [Internet Shortcut Options](#internet-shortcut-options)
    * [Verbosity and Simulation Options](#verbosity-and-simulation-options)
    * [Workarounds](#workarounds)
    * [Video Format Options](#video-format-options)
    * [Subtitle Options](#subtitle-options)
    * [Authentication Options](#authentication-options)
    * [Post-processing Options](#post-processing-options)
    * [SponsorBlock Options](#sponsorblock-options)
    * [Extractor Options](#extractor-options)
    * [Preset Aliases](#preset-aliases)
* [CONFIGURATION](#configuration)
    * [Configuration file encoding](#configuration-file-encoding)
    * [Authentication with netrc](#authentication-with-netrc)
    * [Notes about environment variables](#notes-about-environment-variables)
* [OUTPUT TEMPLATE](#output-template)
    * [Output template examples](#output-template-examples)
* [FORMAT SELECTION](#format-selection)
    * [Filtering Formats](#filtering-formats)
    * [Sorting Formats](#sorting-formats)
    * [Format Selection examples](#format-selection-examples)
* [MODIFYING METADATA](#modifying-metadata)
    * [Modifying metadata examples](#modifying-metadata-examples)
* [EXTRACTOR ARGUMENTS](#extractor-arguments)
* [PLUGINS](#plugins)
    * [Installing Plugins](#installing-plugins)
    * [Developing Plugins](#developing-plugins)
* [EMBEDDING YT-AI](#embedding-yt-ai)
    * [Embedding examples](#embedding-examples)
* [CHANGES FROM YT-DLP](#changes-from-yt-dlp)
    * [New features](#new-features)
    * [Differences in default behavior](#differences-in-default-behavior)
    * [Deprecated options](#deprecated-options)
* [CONTRIBUTING](CONTRIBUTING.md#contributing-to-yt-ai)
    * [Opening an Issue](CONTRIBUTING.md#opening-an-issue)
    * [Developer Instructions](CONTRIBUTING.md#developer-instructions)
* [WIKI](https://github.com/yt-dlp/yt-dlp/wiki)
    * [FAQ](https://github.com/yt-dlp/yt-dlp/wiki/FAQ)
<!-- MANPAGE: END EXCLUDED SECTION -->


# INSTALLATION

<!-- MANPAGE: BEGIN EXCLUDED SECTION -->
[![Windows](https://img.shields.io/badge/-Windows_x64-blue.svg?style=for-the-badge&logo=windows)](https://github.com/CrimsonGlory/yt-ai/releases/latest/download/yt-ai.exe)
[![Unix](https://img.shields.io/badge/-Linux/BSD-red.svg?style=for-the-badge&logo=linux)](https://github.com/CrimsonGlory/yt-ai/releases/latest/download/yt-ai)
[![MacOS](https://img.shields.io/badge/-MacOS-lightblue.svg?style=for-the-badge&logo=apple)](https://github.com/CrimsonGlory/yt-ai/releases/latest/download/yt-ai_macos)
[![PyPI](https://img.shields.io/badge/-PyPI-blue.svg?logo=pypi&labelColor=555555&style=for-the-badge)](https://pypi.org/project/yt-ai)
[![Source Tarball](https://img.shields.io/badge/-Source_tar-green.svg?style=for-the-badge)](https://github.com/CrimsonGlory/yt-ai/releases/latest/download/yt-ai.tar.gz)
[![Other variants](https://img.shields.io/badge/-Other-grey.svg?style=for-the-badge)](#release-files)
[![All versions](https://img.shields.io/badge/-All_Versions-lightgrey.svg?style=for-the-badge)](https://github.com/CrimsonGlory/yt-ai/releases)
<!-- MANPAGE: END EXCLUDED SECTION -->

You can install yt-ai using [the binaries](#release-files), [pip](https://pypi.org/project/yt-ai) or one using a third-party package manager. See [the wiki](https://github.com/yt-dlp/yt-dlp/wiki/Installation) for detailed instructions


<!-- MANPAGE: BEGIN EXCLUDED SECTION -->
## RELEASE FILES

#### Recommended

File|Description
:---|:---
[yt-ai](https://github.com/CrimsonGlory/yt-ai/releases/latest/download/yt-ai)|Platform-independent [zipimport](https://docs.python.org/3/library/zipimport.html) binary. Needs Python (recommended for **Linux/BSD**)
[yt-ai.exe](https://github.com/CrimsonGlory/yt-ai/releases/latest/download/yt-ai.exe)|Windows (Win8+) standalone x64 binary (recommended for **Windows**)
[yt-ai_macos](https://github.com/CrimsonGlory/yt-ai/releases/latest/download/yt-ai_macos)|Universal MacOS (10.15+) standalone executable (recommended for **MacOS**)

#### Alternatives

File|Description
:---|:---
[yt-ai_linux](https://github.com/CrimsonGlory/yt-ai/releases/latest/download/yt-ai_linux)|Linux (glibc 2.17+) standalone x86_64 binary
[yt-ai_linux.zip](https://github.com/CrimsonGlory/yt-ai/releases/latest/download/yt-ai_linux.zip)|Unpackaged Linux (glibc 2.17+) x86_64 executable (no auto-update)
[yt-ai_linux_aarch64](https://github.com/CrimsonGlory/yt-ai/releases/latest/download/yt-ai_linux_aarch64)|Linux (glibc 2.17+) standalone aarch64 binary
[yt-ai_linux_aarch64.zip](https://github.com/CrimsonGlory/yt-ai/releases/latest/download/yt-ai_linux_aarch64.zip)|Unpackaged Linux (glibc 2.17+) aarch64 executable (no auto-update)
[yt-ai_linux_armv7l.zip](https://github.com/CrimsonGlory/yt-ai/releases/latest/download/yt-ai_linux_armv7l.zip)|Unpackaged Linux (glibc 2.31+) armv7l executable (no auto-update)
[yt-ai_musllinux](https://github.com/CrimsonGlory/yt-ai/releases/latest/download/yt-ai_musllinux)|Linux (musl 1.2+) standalone x86_64 binary
[yt-ai_musllinux.zip](https://github.com/CrimsonGlory/yt-ai/releases/latest/download/yt-ai_musllinux.zip)|Unpackaged Linux (musl 1.2+) x86_64 executable (no auto-update)
[yt-ai_musllinux_aarch64](https://github.com/CrimsonGlory/yt-ai/releases/latest/download/yt-ai_musllinux_aarch64)|Linux (musl 1.2+) standalone aarch64 binary
[yt-ai_musllinux_aarch64.zip](https://github.com/CrimsonGlory/yt-ai/releases/latest/download/yt-ai_musllinux_aarch64.zip)|Unpackaged Linux (musl 1.2+) aarch64 executable (no auto-update)
[yt-ai_x86.exe](https://github.com/CrimsonGlory/yt-ai/releases/latest/download/yt-ai_x86.exe)|Windows (Win8+) standalone x86 (32-bit) binary
[yt-ai_win_x86.zip](https://github.com/CrimsonGlory/yt-ai/releases/latest/download/yt-ai_win_x86.zip)|Unpackaged Windows (Win8+) x86 (32-bit) executable (no auto-update)
[yt-ai_arm64.exe](https://github.com/CrimsonGlory/yt-ai/releases/latest/download/yt-ai_arm64.exe)|Windows (Win10+) standalone ARM64 binary
[yt-ai_win_arm64.zip](https://github.com/CrimsonGlory/yt-ai/releases/latest/download/yt-ai_win_arm64.zip)|Unpackaged Windows (Win10+) ARM64 executable (no auto-update)
[yt-ai_win.zip](https://github.com/CrimsonGlory/yt-ai/releases/latest/download/yt-ai_win.zip)|Unpackaged Windows (Win8+) x64 executable (no auto-update)
[yt-ai_macos.zip](https://github.com/CrimsonGlory/yt-ai/releases/latest/download/yt-ai_macos.zip)|Unpackaged MacOS (10.15+) executable (no auto-update)

#### Misc

File|Description
:---|:---
[yt-ai.tar.gz](https://github.com/CrimsonGlory/yt-ai/releases/latest/download/yt-ai.tar.gz)|Source tarball
[SHA2-512SUMS](https://github.com/CrimsonGlory/yt-ai/releases/latest/download/SHA2-512SUMS)|GNU-style SHA512 sums
[SHA2-512SUMS.sig](https://github.com/CrimsonGlory/yt-ai/releases/latest/download/SHA2-512SUMS.sig)|GPG signature file for SHA512 sums
[SHA2-256SUMS](https://github.com/CrimsonGlory/yt-ai/releases/latest/download/SHA2-256SUMS)|GNU-style SHA256 sums
[SHA2-256SUMS.sig](https://github.com/CrimsonGlory/yt-ai/releases/latest/download/SHA2-256SUMS.sig)|GPG signature file for SHA256 sums

The public key that can be used to verify the GPG signatures is [available here](https://github.com/CrimsonGlory/yt-ai/blob/master/public.key)
Example usage:
```
curl -L https://github.com/CrimsonGlory/yt-ai/raw/master/public.key | gpg --import
gpg --verify SHA2-256SUMS.sig SHA2-256SUMS
gpg --verify SHA2-512SUMS.sig SHA2-512SUMS
```

#### Licensing

While yt-ai is licensed under the [Unlicense](LICENSE), many of the release files contain code from other projects with different licenses.

Most notably, the PyInstaller-bundled executables include GPLv3+ licensed code, and as such the combined work is licensed under [GPLv3+](https://www.gnu.org/licenses/gpl-3.0.html).

The zipimport Unix executable (`yt-ai`) and release tarball (`yt-ai.tar.gz`) contain [ISC](https://github.com/meriyah/meriyah/blob/main/LICENSE.md) licensed code from [`meriyah`](https://github.com/meriyah/meriyah) and [MIT](https://github.com/davidbonnet/astring/blob/main/LICENSE) licensed code from [`astring`](https://github.com/davidbonnet/astring).

See [THIRD_PARTY_LICENSES.txt](THIRD_PARTY_LICENSES.txt) for more details.

The git repository, the PyPI source distribution and the PyPI built distribution (wheel) only contain code licensed under the [Unlicense](LICENSE).

<!-- MANPAGE: END EXCLUDED SECTION -->

**Note**: The manpages, shell completion (autocomplete) files etc. are available inside the [source tarball](https://github.com/CrimsonGlory/yt-ai/releases/latest/download/yt-ai.tar.gz)


## UPDATE
You can use `yt-ai -U` to update if you are using the [release binaries](#release-files)

If you [installed with pip](https://github.com/yt-dlp/yt-dlp/wiki/Installation#with-pip), simply re-run the same command that was used to install the program

For other third-party package managers, see [the wiki](https://github.com/yt-dlp/yt-dlp/wiki/Installation#third-party-package-managers) or refer to their documentation

<a id="update-channels"></a>

There are currently three release channels for binaries: `stable`, `nightly` and `master`.

* `stable` is the default channel, which offers releases published on a (mostly) monthly schedule. While it is named `stable` due to many of its changes having been tested by users of the `nightly` or `master` release channels, the latest `stable` release is often "stale" and prone to external breakage (i.e. sites changing things on their end and breaking yt-ai).
* The `nightly` channel offers releases that publish shortly before midnight UTC on any day that sees changes to the codebase. This channel serves as a snapshot of the project's development, and it is the **recommended channel for regular users** of yt-ai. The `nightly` releases are available from [yt-dlp/yt-dlp-nightly-builds](https://github.com/yt-dlp/yt-dlp-nightly-builds/releases) or as development releases of the `yt-ai` PyPI package (which can be installed with pip's `--pre` flag).
* The `master` channel offers "canary" releases that publish after each push to the master branch. This channel will always provide the very latest fixes and features, but may be prone to bugs or regressions. The `master` releases are available from [yt-dlp/yt-dlp-master-builds](https://github.com/yt-dlp/yt-dlp-master-builds/releases).

When using `--update`/`-U`, a release binary will only update to its current channel.
`--update-to CHANNEL` can be used to switch to a different channel when a newer version is available. `--update-to [CHANNEL@]TAG` can also be used to upgrade or downgrade to specific tags from a channel.

You may also use `--update-to <repository>` (`<owner>/<repository>`) to update to a channel on a completely different repository. Be careful with what repository you are updating to though, there is no verification done for binaries from different repositories.

Example usage:

* `yt-ai --update-to master` switch to the `master` channel and update to its latest release
* `yt-ai --update-to stable@2023.07.06` upgrade/downgrade to release to `stable` channel tag `2023.07.06`
* `yt-ai --update-to 2023.10.07` upgrade/downgrade to tag `2023.10.07` if it exists on the current channel
* `yt-ai --update-to example/yt-ai@2023.09.24` upgrade/downgrade to the release from the `example/yt-ai` repository, tag `2023.09.24`

**Important**: Any user experiencing an issue with the `stable` release should install or update to the `nightly` release before submitting a bug report:
```
# To update to nightly from stable executable/binary:
yt-ai --update-to nightly

# To install nightly with pip:
python -m pip install -U --pre "yt-ai[default]"
```

When running a yt-ai version that is older than 90 days, you will see a warning message suggesting to update to the latest version.
You can suppress this warning by adding `--no-update` to your command or configuration file.

## DEPENDENCIES
Python versions 3.10+ (CPython) and 3.11+ (PyPy) are supported. Other versions and implementations may or may not work correctly.

<!-- Python 3.5+ uses VC++14 and it is already embedded in the binary created
<!x-- https://www.microsoft.com/en-us/download/details.aspx?id=26999 --x>
On Windows, [Microsoft Visual C++ 2010 SP1 Redistributable Package (x86)](https://download.microsoft.com/download/1/6/5/165255E7-1014-4D0A-B094-B6A430A6BFFC/vcredist_x86.exe) is also necessary to run yt-ai. You probably already have this, but if the executable throws an error due to missing `MSVCR100.dll` you need to install it manually.
-->

While all the other dependencies are optional, `ffmpeg`, `ffprobe`, `yt-dlp-ejs` and a supported JavaScript runtime/engine are highly recommended

### Strongly recommended

* [**ffmpeg** and **ffprobe**](https://www.ffmpeg.org) - Required for [merging separate video and audio files](#format-selection), as well as for various [post-processing](#post-processing-options) tasks. License [depends on the build](https://www.ffmpeg.org/legal.html)

    Since ffmpeg is such an important dependency, we provide our own builds at [yt-dlp/FFmpeg-Builds](https://github.com/yt-dlp/FFmpeg-Builds). In the past, patches were applied to these builds in order to fix common issues for yt-ai users, but currently our builds are equivalent to upstream ffmpeg. See [the readme](https://github.com/yt-dlp/FFmpeg-Builds#patches-applied) for details

    **Important**: What you need is ffmpeg *binary*, **NOT** [the Python package of the same name](https://pypi.org/project/ffmpeg)

* [**yt-dlp-ejs**](https://github.com/yt-dlp/ejs) - Required for full YouTube support. Licensed under [Unlicense](https://github.com/yt-dlp/ejs/blob/main/LICENSE), bundles [MIT](https://github.com/davidbonnet/astring/blob/main/LICENSE) and [ISC](https://github.com/meriyah/meriyah/blob/main/LICENSE.md) components.

    A JavaScript runtime/engine like [**deno**](https://deno.land) (recommended), [**node.js**](https://nodejs.org), [**bun**](https://bun.sh), or [**QuickJS**](https://bellard.org/quickjs/) is also required to run yt-dlp-ejs. See [the wiki](https://github.com/yt-dlp/yt-dlp/wiki/EJS).

### Networking
* [**certifi**](https://github.com/certifi/python-certifi)\* - Provides Mozilla's root certificate bundle. Licensed under [MPLv2](https://github.com/certifi/python-certifi/blob/master/LICENSE)
* [**brotli**](https://github.com/google/brotli)\* or [**brotlicffi**](https://github.com/python-hyper/brotlicffi) - [Brotli](https://en.wikipedia.org/wiki/Brotli) content encoding support. Both licensed under MIT <sup>[1](https://github.com/google/brotli/blob/master/LICENSE) [2](https://github.com/python-hyper/brotlicffi/blob/master/LICENSE) </sup>
* [**websockets**](https://github.com/aaugustin/websockets)\* - For downloading over websocket. Licensed under [BSD-3-Clause](https://github.com/aaugustin/websockets/blob/main/LICENSE)
* [**requests**](https://github.com/psf/requests)\* - HTTP library. For HTTPS proxy and persistent connections support. Licensed under [Apache-2.0](https://github.com/psf/requests/blob/main/LICENSE)

#### Impersonation

The following provide support for impersonating browser requests. This may be required for some sites that employ TLS fingerprinting.

* [**curl_cffi**](https://github.com/lexiforest/curl_cffi) (recommended) - Python binding for [curl-impersonate](https://github.com/lexiforest/curl-impersonate). Provides impersonation targets for Chrome, Edge and Safari. Licensed under [MIT](https://github.com/lexiforest/curl_cffi/blob/main/LICENSE)
  * Can be installed with the `curl-cffi` extra, e.g. `pip install "yt-ai[default,curl-cffi]"`
  * Currently included in most builds *except* `yt-ai` (Unix zipimport binary) and `yt-ai_x86` (Windows 32-bit)


### Metadata

* [**mutagen**](https://github.com/quodlibet/mutagen)\* - For `--embed-thumbnail` in certain formats. Licensed under [GPLv2+](https://github.com/quodlibet/mutagen/blob/master/COPYING)
* [**AtomicParsley**](https://github.com/wez/atomicparsley) - For `--embed-thumbnail` in `mp4`/`m4a` files when `mutagen`/`ffmpeg` cannot. Licensed under [GPLv2+](https://github.com/wez/atomicparsley/blob/master/COPYING)
* [**xattr**](https://github.com/xattr/xattr), [**pyxattr**](https://github.com/iustin/pyxattr) or [**setfattr**](http://savannah.nongnu.org/projects/attr) - For writing xattr metadata (`--xattrs`) on **Mac** and **BSD**. Licensed under [MIT](https://github.com/xattr/xattr/blob/master/LICENSE.txt), [LGPL2.1](https://github.com/iustin/pyxattr/blob/master/COPYING) and [GPLv2+](http://git.savannah.nongnu.org/cgit/attr.git/tree/doc/COPYING) respectively

### Misc

* [**pycryptodomex**](https://github.com/Legrandin/pycryptodome)\* - For decrypting AES-128 HLS streams and various other data. Licensed under [BSD-2-Clause](https://github.com/Legrandin/pycryptodome/blob/master/LICENSE.rst)
* [**phantomjs**](https://github.com/ariya/phantomjs) - Used in some extractors where JavaScript needs to be run. No longer used for YouTube. To be deprecated in the near future. Licensed under [BSD-3-Clause](https://github.com/ariya/phantomjs/blob/master/LICENSE.BSD)
* [**secretstorage**](https://github.com/mitya57/secretstorage)\* - For `--cookies-from-browser` to access the **Gnome** keyring while decrypting cookies of **Chromium**-based browsers on **Linux**. Licensed under [BSD-3-Clause](https://github.com/mitya57/secretstorage/blob/master/LICENSE)
* Any external downloader that you want to use with `--downloader`

### Deprecated

* [**rtmpdump**](http://rtmpdump.mplayerhq.hu) - For downloading `rtmp` streams. ffmpeg can be used instead with `--downloader ffmpeg`. Licensed under [GPLv2+](http://rtmpdump.mplayerhq.hu)

To use or redistribute the dependencies, you must agree to their respective licensing terms.

The standalone release binaries are built with the Python interpreter and the packages marked with **\*** included.

If you do not have the necessary dependencies for a task you are attempting, yt-ai will warn you. All the currently available dependencies are visible at the top of the `--verbose` output


## COMPILE

### Standalone PyInstaller Builds
To build the standalone executable, you must have Python and `pyinstaller` (plus any of yt-ai's [optional dependencies](#dependencies) if needed). The executable will be built for the same CPU architecture as the Python used.

You can run the following commands:

```
python devscripts/install_deps.py --include-group pyinstaller
python devscripts/make_lazy_extractors.py
python -m bundle.pyinstaller
```

On some systems, you may need to use `py` or `python3` instead of `python`.

`python -m bundle.pyinstaller` accepts any arguments that can be passed to `pyinstaller`, such as `--onefile/-F` or `--onedir/-D`, which is further [documented here](https://pyinstaller.org/en/stable/usage.html#what-to-generate).

**Note**: Pyinstaller versions below 4.4 [do not support](https://github.com/pyinstaller/pyinstaller#requirements-and-tested-platforms) Python installed from the Windows store without using a virtual environment.

**Important**: Running `pyinstaller` directly **instead of** using `python -m bundle.pyinstaller` is **not** officially supported. This may or may not work correctly.

### Platform-independent Binary (UNIX)
You will need the build tools `python` (3.10+), `zip`, `make` (GNU), `pandoc`\* and `pytest`\*.

After installing these, simply run `make`.

You can also run `make yt-ai` instead to compile only the binary without updating any of the additional files. (The build tools marked with **\*** are not needed for this)

### Related scripts

* **`devscripts/install_deps.py`** - Install dependencies for yt-ai.
* **`devscripts/update-version.py`** - Update the version number based on the current date.
* **`devscripts/set-variant.py`** - Set the build variant of the executable.
* **`devscripts/make_changelog.py`** - Create a markdown changelog using short commit messages and update `CONTRIBUTORS` file.
* **`devscripts/make_lazy_extractors.py`** - Create lazy extractors. Running this before building the binaries (any variant) will improve their startup performance. Set the environment variable `YTDLP_NO_LAZY_EXTRACTORS` to something nonempty to forcefully disable lazy extractor loading.

Note: See their `--help` for more info.

### Forking the project
If you fork the project on GitHub, you can run your fork's [build workflow](.github/workflows/build.yml) to automatically build the selected version(s) as artifacts. Alternatively, you can run the [release workflow](.github/workflows/release.yml) or enable the [nightly workflow](.github/workflows/release-nightly.yml) to create full (pre-)releases.

# USAGE AND OPTIONS

<!-- MANPAGE: BEGIN EXCLUDED SECTION -->
    yt-ai [OPTIONS] [--] URL [URL...]

Tip: Use `CTRL`+`F` (or `Command`+`F`)  to search by keywords
<!-- MANPAGE: END EXCLUDED SECTION -->

<!-- Auto generated -->
## General Options:
    -h, --help                      Print this help text and exit
    --version                       Print program version and exit
    -U, --update                    Update this program to the latest version
    --no-update                     Do not check for updates (default)
    --update-to [CHANNEL]@[TAG]     Upgrade/downgrade to a specific version.
                                    CHANNEL can be a repository as well. CHANNEL
                                    and TAG default to "stable" and "latest"
                                    respectively if omitted; See "UPDATE" for
                                    details. Supported channels: stable,
                                    nightly, master
    -i, --ignore-errors             Ignore download and postprocessing errors.
                                    The download will be considered successful
                                    even if the postprocessing fails
    --no-abort-on-error             Continue with next video on download errors;
                                    e.g. to skip unavailable videos in a
                                    playlist (default)
    --abort-on-error                Abort downloading of further videos if an
                                    error occurs (Alias: --no-ignore-errors)
    --list-extractors               List all supported extractors and exit
    --extractor-descriptions        Output descriptions of all supported
                                    extractors and exit
    --use-extractors NAMES          Extractor names to use separated by commas.
                                    You can also use regexes, "all", "default"
                                    and "end" (end URL matching); e.g. --ies
                                    "holodex.*,end,youtube". Prefix the name
                                    with a "-" to exclude it, e.g. --ies
                                    default,-generic. Use --list-extractors for
                                    a list of extractor names. (Alias: --ies)
    --default-search PREFIX         Use this prefix for unqualified URLs. E.g.
                                    "gvsearch2:python" downloads two videos from
                                    google videos for the search term "python".
                                    Use the value "auto" to let yt-ai guess
                                    ("auto_warning" to emit a warning when
                                    guessing). "error" just throws an error. The
                                    default value "fixup_error" repairs broken
                                    URLs, but emits an error if this is not
                                    possible instead of searching
    --ignore-config                 Don't load any more configuration files
                                    except those given to --config-locations.
                                    For backward compatibility, if this option
                                    is found inside the system configuration
                                    file, the user configuration is not loaded.
                                    (Alias: --no-config)
    --no-config-locations           Do not load any custom configuration files
                                    (default). When given inside a configuration
                                    file, ignore all previous --config-locations
                                    defined in the current file
    --config-locations PATH         Location of the main configuration file;
                                    either the path to the config or its
                                    containing directory ("-" for stdin). Can be
                                    used multiple times and inside other
                                    configuration files
    --plugin-dirs DIR               Path to an additional directory to search
                                    for plugins. This option can be used
                                    multiple times to add multiple directories.
                                    Use "default" to search the default plugin
                                    directories (default)
    --no-plugin-dirs                Clear plugin directories to search,
                                    including defaults and those provided by
                                    previous --plugin-dirs
    --js-runtimes RUNTIME[:PATH]    Additional JavaScript runtime to enable,
                                    with an optional location for the runtime
                                    (either the path to the binary or its
                                    containing directory). This option can be
                                    used multiple times to enable multiple
                                    runtimes. Supported runtimes are (in order
                                    of priority, from highest to lowest): deno,
                                    node, quickjs, bun. Only "deno" is enabled
                                    by default. The highest priority runtime
                                    that is both enabled and available will be
                                    used. In order to use a lower priority
                                    runtime when "deno" is available, --no-js-
                                    runtimes needs to be passed before enabling
                                    other runtimes
    --no-js-runtimes                Clear JavaScript runtimes to enable,
                                    including defaults and those provided by
                                    previous --js-runtimes
    --remote-components COMPONENT   Remote components to allow yt-ai to fetch
                                    when required. This option is currently not
                                    needed if you are using an official
                                    executable or have the requisite version of
                                    the yt-dlp-ejs package installed. You can
                                    use this option multiple times to allow
                                    multiple components. Supported values:
                                    ejs:npm (external JavaScript components from
                                    npm), ejs:github (external JavaScript
                                    components from yt-dlp-ejs GitHub). By
                                    default, no remote components are allowed
    --no-remote-components          Disallow fetching of all remote components,
                                    including any previously allowed by
                                    --remote-components or defaults.
    --flat-playlist                 Do not extract a playlist's URL result
                                    entries; some entry metadata may be missing
                                    and downloading may be bypassed
    --no-flat-playlist              Fully extract the videos of a playlist
                                    (default)
    --live-from-start               Download livestreams from the start.
                                    Currently experimental and only supported
                                    for YouTube, Twitch, TVer, and mellow-fan
    --no-live-from-start            Download livestreams from the current time
                                    (default)
    --wait-for-video MIN[-MAX]      Wait for scheduled streams to become
                                    available. Pass the minimum number of
                                    seconds (or range) to wait between retries
    --no-wait-for-video             Do not wait for scheduled streams (default)
    --mark-watched                  Mark videos watched (even with --simulate)
    --no-mark-watched               Do not mark videos watched (default)
    --color [STREAM:]POLICY         Whether to emit color codes in output,
                                    optionally prefixed by the STREAM (stdout or
                                    stderr) to apply the setting to. Can be one
                                    of "always", "auto" (default), "never", or
                                    "no_color" (use non color terminal
                                    sequences). Use "auto-tty" or "no_color-tty"
                                    to decide based on terminal support only.
                                    Can be used multiple times
    --compat-options OPTS           Options that can help keep compatibility
                                    with youtube-dl or youtube-dlc
                                    configurations by reverting some of the
                                    changes made in yt-ai. See "Differences in
                                    default behavior" for details
    --alias ALIASES OPTIONS         Create aliases for an option string. Unless
                                    an alias starts with a dash "-", it is
                                    prefixed with "--". Arguments are parsed
                                    according to the Python string formatting
                                    mini-language. E.g. --alias get-audio,-X "-S
                                    aext:{0},abr -x --audio-format {0}" creates
                                    options "--get-audio" and "-X" that takes an
                                    argument (ARG0) and expands to "-S
                                    aext:ARG0,abr -x --audio-format ARG0". All
                                    defined aliases are listed in the --help
                                    output. Alias options can trigger more
                                    aliases; so be careful to avoid defining
                                    recursive options. As a safety measure, each
                                    alias may be triggered a maximum of 100
                                    times. This option can be used multiple times
    -t, --preset-alias PRESET       Applies a predefined set of options. e.g.
                                    --preset-alias mp3. The following presets
                                    are available: mp3, aac, mp4, mkv, sleep.
                                    See the "Preset Aliases" section at the end
                                    for more info. This option can be used
                                    multiple times

## Network Options:
    --proxy URL                     Use the specified HTTP/HTTPS/SOCKS proxy. To
                                    enable SOCKS proxy, specify a proper scheme,
                                    e.g. socks5://user:pass@127.0.0.1:1080/.
                                    Pass in an empty string (--proxy "") for
                                    direct connection
    --socket-timeout SECONDS        Time to wait before giving up, in seconds
    --source-address IP             Client-side IP address to bind to
    --impersonate CLIENT[:OS]       Client to impersonate for requests. E.g.
                                    chrome, chrome-110, chrome:windows-10. Pass
                                    --impersonate="" to impersonate any client.
                                    Note that forcing impersonation for all
                                    requests may have a detrimental impact on
                                    download speed and stability
    --list-impersonate-targets      List available clients to impersonate.
    -4, --force-ipv4                Make all connections via IPv4
    -6, --force-ipv6                Make all connections via IPv6
    --enable-file-urls              Enable file:// URLs. This is disabled by
                                    default for security reasons.

## Geo-restriction:
    --geo-verification-proxy URL    Use this proxy to verify the IP address for
                                    some geo-restricted sites. The default proxy
                                    specified by --proxy (or none, if the option
                                    is not present) is used for the actual
                                    downloading
    --xff VALUE                     How to fake X-Forwarded-For HTTP header to
                                    try bypassing geographic restriction. One of
                                    "default" (only when known to be useful),
                                    "never", an IP block in CIDR notation, or a
                                    two-letter ISO 3166-2 country code

## Video Selection:
    -I, --playlist-items ITEM_SPEC  Comma-separated playlist_index of the items
                                    to download. You can specify a range using
                                    "[START]:[STOP][:STEP]". For backward
                                    compatibility, START-STOP is also supported.
                                    Use negative indices to count from the right
                                    and negative STEP to download in reverse
                                    order. E.g. "-I 1:3,7,-5::2" used on a
                                    playlist of size 15 will download the items
                                    at index 1,2,3,7,11,13,15
    --min-filesize SIZE             Abort download if filesize is smaller than
                                    SIZE, e.g. 50k or 44.6M
    --max-filesize SIZE             Abort download if filesize is larger than
                                    SIZE, e.g. 50k or 44.6M
    --date DATE                     Download only videos uploaded on this date.
                                    The date can be "YYYYMMDD" or in the format
                                    [now|today|yesterday][-N[day|week|month|year]].
                                    E.g. "--date today-2weeks" downloads only
                                    videos uploaded on the same day two weeks ago
    --datebefore DATE               Download only videos uploaded on or before
                                    this date. The date formats accepted are the
                                    same as --date
    --dateafter DATE                Download only videos uploaded on or after
                                    this date. The date formats accepted are the
                                    same as --date
    --match-filters FILTER          Generic video filter. Any "OUTPUT TEMPLATE"
                                    field can be compared with a number or a
                                    string using the operators defined in
                                    "Filtering Formats". You can also simply
                                    specify a field to match if the field is
                                    present, use "!field" to check if the field
                                    is not present, and "&" to check multiple
                                    conditions. Use a "\" to escape "&" or
                                    quotes if needed. If used multiple times,
                                    the filter matches if at least one of the
                                    conditions is met. E.g. --match-filters
                                    !is_live --match-filters "like_count>?100 &
                                    description~='(?i)\bcats \& dogs\b'" matches
                                    only videos that are not live OR those that
                                    have a like count more than 100 (or the like
                                    field is not available) and also has a
                                    description that contains the phrase "cats &
                                    dogs" (caseless). Use "--match-filters -" to
                                    interactively ask whether to download each
                                    video
    --no-match-filters              Do not use any --match-filters (default)
    --break-match-filters FILTER    Same as "--match-filters" but stops the
                                    download process when a video is rejected
    --no-break-match-filters        Do not use any --break-match-filters (default)
    --no-playlist                   Download only the video, if the URL refers
                                    to a video and a playlist
    --yes-playlist                  Download the playlist, if the URL refers to
                                    a video and a playlist
    --age-limit YEARS               Download only videos suitable for the given
                                    age
    --download-archive FILE         Download only videos not listed in the
                                    archive file. Record the IDs of all
                                    downloaded videos in it
    --no-download-archive           Do not use archive file (default)
    --max-downloads NUMBER          Abort after downloading NUMBER files
    --break-on-existing             Stop the download process when encountering
                                    a file that is in the archive supplied with
                                    the --download-archive option
    --no-break-on-existing          Do not stop the download process when
                                    encountering a file that is in the archive
                                    (default)
    --break-per-input               Alters --max-downloads, --break-on-existing,
                                    --break-match-filters, and autonumber to
                                    reset per input URL
    --no-break-per-input            --break-on-existing and similar options
                                    terminates the entire download queue
    --skip-playlist-after-errors N  Number of allowed failures until the rest of
                                    the playlist is skipped

## Download Options:
    -N, --concurrent-fragments N    Number of fragments of a dash/hlsnative
                                    video that should be downloaded concurrently
                                    (default is 1)
    -r, --limit-rate RATE           Maximum download rate in bytes per second,
                                    e.g. 50K or 4.2M
    --throttled-rate RATE           Minimum download rate in bytes per second
                                    below which throttling is assumed and the
                                    video data is re-extracted, e.g. 100K
    -R, --retries RETRIES           Number of retries (default is 10), or
                                    "infinite"
    --file-access-retries RETRIES   Number of times to retry on file access
                                    error (default is 3), or "infinite"
    --fragment-retries RETRIES      Number of retries for a fragment (default is
                                    10), or "infinite" (DASH, hlsnative and ISM)
    --retry-sleep [TYPE:]EXPR       Time to sleep between retries in seconds
                                    (optionally) prefixed by the type of retry
                                    (http (default), fragment, file_access,
                                    extractor) to apply the sleep to. EXPR can
                                    be a number, linear=START[:END[:STEP=1]] or
                                    exp=START[:END[:BASE=2]]. This option can be
                                    used multiple times to set the sleep for the
                                    different retry types, e.g. --retry-sleep
                                    linear=1::2 --retry-sleep fragment:exp=1:20
    --skip-unavailable-fragments    Skip unavailable fragments for DASH,
                                    hlsnative and ISM downloads (default)
                                    (Alias: --no-abort-on-unavailable-fragments)
    --abort-on-unavailable-fragments
                                    Abort download if a fragment is unavailable
                                    (Alias: --no-skip-unavailable-fragments)
    --keep-fragments                Keep downloaded fragments on disk after
                                    downloading is finished
    --no-keep-fragments             Delete downloaded fragments after
                                    downloading is finished (default)
    --buffer-size SIZE              Size of download buffer, e.g. 1024 or 16K
                                    (default is 1024)
    --resize-buffer                 The buffer size is automatically resized
                                    from an initial value of --buffer-size
                                    (default)
    --no-resize-buffer              Do not automatically adjust the buffer size
    --http-chunk-size SIZE          Size of a chunk for chunk-based HTTP
                                    downloading, e.g. 10485760 or 10M (default
                                    is disabled). May be useful for bypassing
                                    bandwidth throttling imposed by a webserver
                                    (experimental)
    --playlist-random               Download playlist videos in random order
    --lazy-playlist                 Process entries in the playlist as they are
                                    received. This disables n_entries,
                                    --playlist-random and --playlist-reverse
    --no-lazy-playlist              Process videos in the playlist only after
                                    the entire playlist is parsed (default)
    --hls-use-mpegts                Use the mpegts container for HLS videos;
                                    allowing some players to play the video
                                    while downloading, and reducing the chance
                                    of file corruption if download is
                                    interrupted. This is enabled by default for
                                    live streams
    --no-hls-use-mpegts             Do not use the mpegts container for HLS
                                    videos. This is default when not downloading
                                    live streams
    --download-sections REGEX       Download only chapters that match the
                                    regular expression. A "*" prefix denotes
                                    time-range instead of chapter. Negative
                                    timestamps are calculated from the end.
                                    "*from-url" can be used to download between
                                    the "start_time" and "end_time" extracted
                                    from the URL. Needs ffmpeg. This option can
                                    be used multiple times to download multiple
                                    sections, e.g. --download-sections
                                    "*10:15-inf" --download-sections "intro"
    --downloader [PROTO:]NAME       Name or path of the external downloader to
                                    use (optionally) prefixed by the protocols
                                    (http, ftp, m3u8, dash, rtmp) to use it for.
                                    Currently supports native, aria2c, axel,
                                    curl, ffmpeg, httpie, wget. You can use this
                                    option multiple times to set different
                                    downloaders for different protocols. E.g.
                                    --downloader aria2c --downloader
                                    "dash,m3u8:native" will use aria2c for
                                    http/ftp downloads, and the native
                                    downloader for dash/m3u8 downloads (Alias:
                                    --external-downloader)
    --downloader-args NAME:ARGS     Give these arguments to the external
                                    downloader. Specify the downloader name and
                                    the arguments separated by a colon ":". For
                                    ffmpeg, arguments can be passed to different
                                    positions using the same syntax as
                                    --postprocessor-args. You can use this
                                    option multiple times to give different
                                    arguments to different downloaders (Alias:
                                    --external-downloader-args)

## Filesystem Options:
    -a, --batch-file FILE           File containing URLs to download ("-" for
                                    stdin), one URL per line. Lines starting
                                    with "#", ";" or "]" are considered as
                                    comments and ignored
    --no-batch-file                 Do not read URLs from batch file (default)
    -P, --paths [TYPES:]PATH        The paths where the files should be
                                    downloaded. Specify the type of file and the
                                    path separated by a colon ":". All the same
                                    TYPES as --output are supported.
                                    Additionally, you can also provide "home"
                                    (default) and "temp" paths. All intermediary
                                    files are first downloaded to the temp path
                                    and then the final files are moved over to
                                    the home path after download is finished.
                                    This option is ignored if --output is an
                                    absolute path
    -o, --output [TYPES:]TEMPLATE   Output filename template; see "OUTPUT
                                    TEMPLATE" for details
    --output-na-placeholder TEXT    Placeholder for unavailable fields in
                                    --output (default: "NA")
    --restrict-filenames            Restrict filenames to only ASCII characters,
                                    and avoid "&" and spaces in filenames
    --no-restrict-filenames         Allow Unicode characters, "&" and spaces in
                                    filenames (default)
    --windows-filenames             Force filenames to be Windows-compatible
    --no-windows-filenames          Sanitize filenames only minimally
    --trim-filenames LENGTH         Limit the filename length (excluding
                                    extension) to the specified number of
                                    characters
    -w, --no-overwrites             Do not overwrite any files
    --force-overwrites              Overwrite all video and metadata files. This
                                    option includes --no-continue
    --no-force-overwrites           Do not overwrite the video, but overwrite
                                    related files (default)
    -c, --continue                  Resume partially downloaded files/fragments
                                    (default)
    --no-continue                   Do not resume partially downloaded
                                    fragments. If the file is not fragmented,
                                    restart download of the entire file
    --part                          Use .part files instead of writing directly
                                    into output file (default)
    --no-part                       Do not use .part files - write directly into
                                    output file
    --mtime                         Use the Last-modified header to set the file
                                    modification time
    --no-mtime                      Do not use the Last-modified header to set
                                    the file modification time (default)
    --write-description             Write video description to a .description file
    --no-write-description          Do not write video description (default)
    --write-info-json               Write video metadata to a .info.json file
                                    (this may contain personal information)
    --no-write-info-json            Do not write video metadata (default)
    --write-playlist-metafiles      Write playlist metadata in addition to the
                                    video metadata when using --write-info-json,
                                    --write-description etc. (default)
    --no-write-playlist-metafiles   Do not write playlist metadata when using
                                    --write-info-json, --write-description etc.
    --clean-info-json               Remove some internal metadata such as
                                    filenames from the infojson (default)
    --no-clean-info-json            Write all fields to the infojson
    --write-comments                Retrieve video comments to be placed in the
                                    infojson. The comments are fetched even
                                    without this option if the extraction is
                                    known to be quick (Alias: --get-comments)
    --no-write-comments             Do not retrieve video comments unless the
                                    extraction is known to be quick (Alias:
                                    --no-get-comments)
    --load-info-json FILE           JSON file containing the video information
                                    (created with the "--write-info-json" option)
    --cookies FILE                  Netscape formatted file to read cookies from
                                    and dump cookie jar in
    --no-cookies                    Do not read/dump cookies from/to file
                                    (default)
    --cookies-from-browser BROWSER[+KEYRING][:PROFILE][::CONTAINER]
                                    The name of the browser to load cookies
                                    from. Currently supported browsers are:
                                    brave, chrome, chromium, edge, firefox,
                                    opera, safari, vivaldi, whale. Optionally,
                                    the KEYRING used for decrypting Chromium
                                    cookies on Linux, the name/path of the
                                    PROFILE to load cookies from, and the
                                    CONTAINER name (if Firefox) ("none" for no
                                    container) can be given with their
                                    respective separators. By default, all
                                    containers of the most recently accessed
                                    profile are used. Currently supported
                                    keyrings are: basictext, gnomekeyring,
                                    kwallet, kwallet5, kwallet6
    --no-cookies-from-browser       Do not load cookies from browser (default)
    --cache-dir DIR                 Location in the filesystem where yt-ai can
                                    store some downloaded information (such as
                                    client ids and signatures) permanently. By
                                    default ${XDG_CACHE_HOME}/yt-ai
    --no-cache-dir                  Disable filesystem caching
    --rm-cache-dir                  Delete all filesystem cache files

## Thumbnail Options:
    --write-thumbnail               Write thumbnail image to disk
    --no-write-thumbnail            Do not write thumbnail image to disk (default)
    --write-all-thumbnails          Write all thumbnail image formats to disk
    --list-thumbnails               List available thumbnails of each video.
                                    Simulate unless --no-simulate is used

## Internet Shortcut Options:
    --write-link                    Write an internet shortcut file, depending
                                    on the current platform (.url, .webloc or
                                    .desktop). The URL may be cached by the OS
    --write-url-link                Write a .url Windows internet shortcut. The
                                    OS caches the URL based on the file path
    --write-webloc-link             Write a .webloc macOS internet shortcut
    --write-desktop-link            Write a .desktop Linux internet shortcut

## Verbosity and Simulation Options:
    -q, --quiet                     Activate quiet mode. If used with --verbose,
                                    print the log to stderr
    --no-quiet                      Deactivate quiet mode. (Default)
    --no-warnings                   Ignore warnings
    -s, --simulate                  Do not download the video and do not write
                                    anything to disk
    --no-simulate                   Download the video even if printing/listing
                                    options are used
    --ignore-no-formats-error       Ignore "No video formats" error. Useful for
                                    extracting metadata even if the videos are
                                    not actually available for download
                                    (experimental)
    --no-ignore-no-formats-error    Throw error when no downloadable video
                                    formats are found (default)
    --skip-download                 Do not download the video but write all
                                    related files (Alias: --no-download)
    -O, --print [WHEN:]TEMPLATE     Field name or output template to print to
                                    screen, optionally prefixed with when to
                                    print it, separated by a ":". Supported
                                    values of "WHEN" are the same as that of
                                    --use-postprocessor (default: video).
                                    Implies --quiet. Implies --simulate unless
                                    --no-simulate or later stages of WHEN are
                                    used. This option can be used multiple times
    --print-to-file [WHEN:]TEMPLATE FILE
                                    Append given template to the file. The
                                    values of WHEN and TEMPLATE are the same as
                                    that of --print. FILE uses the same syntax
                                    as the output template. This option can be
                                    used multiple times
    -j, --dump-json                 Quiet, but print JSON information for each
                                    video. Simulate unless --no-simulate is
                                    used. See "OUTPUT TEMPLATE" for a
                                    description of available keys
    -J, --dump-single-json          Quiet, but print JSON information for each
                                    URL or infojson passed. Simulate unless
                                    --no-simulate is used. If the URL refers to
                                    a playlist, the whole playlist information
                                    is dumped in a single line
    --force-write-archive           Force download archive entries to be written
                                    as far as no errors occur, even if -s or
                                    another simulation option is used (Alias:
                                    --force-download-archive)
    --newline                       Output progress bar as new lines
    --no-progress                   Do not print progress bar
    --progress                      Show progress bar, even if in quiet mode
    --console-title                 Display progress in console titlebar
    --progress-template [TYPES:]TEMPLATE
                                    Template for progress outputs, optionally
                                    prefixed with one of "download:" (default),
                                    "download-title:" (the console title),
                                    "postprocess:",  or "postprocess-title:".
                                    The video's fields are accessible under the
                                    "info" key and the progress attributes are
                                    accessible under "progress" key. E.g.
                                    --console-title --progress-template
                                    "download-title:%(info.id)s-%(progress.eta)s"
    --progress-delta SECONDS        Time between progress output (default: 0)
    -v, --verbose                   Print various debugging information
    --dump-pages                    Print downloaded pages encoded using base64
                                    to debug problems (very verbose)
    --write-pages                   Write downloaded intermediary pages to files
                                    in the current directory to debug problems
    --print-traffic                 Display sent and read HTTP traffic

## Workarounds:
    --encoding ENCODING             Force the specified encoding (experimental)
    --legacy-server-connect         Explicitly allow HTTPS connection to servers
                                    that do not support RFC 5746 secure
                                    renegotiation
    --no-check-certificates         Suppress HTTPS certificate validation
    --prefer-insecure               Use an unencrypted connection to retrieve
                                    information about the video
    --add-headers FIELD:VALUE       Specify a custom HTTP header and its value,
                                    separated by a colon ":". You can use this
                                    option multiple times
    --bidi-workaround               Work around terminals that lack
                                    bidirectional text support. Requires bidiv
                                    or fribidi executable in PATH
    --sleep-requests SECONDS        Number of seconds to sleep between requests
                                    during data extraction
    --sleep-interval SECONDS        Number of seconds to sleep before each
                                    download. This is the minimum time to sleep
                                    when used along with --max-sleep-interval
                                    (Alias: --min-sleep-interval)
    --max-sleep-interval SECONDS    Maximum number of seconds to sleep. Can only
                                    be used along with --min-sleep-interval
    --sleep-subtitles SECONDS       Number of seconds to sleep before each
                                    subtitle download

## Video Format Options:
    -f, --format FORMAT             Video format code, see "FORMAT SELECTION"
                                    for more details
    -S, --format-sort SORTORDER     Sort the formats by the fields given, see
                                    "Sorting Formats" for more details
    --format-sort-reset             Disregard previous user specified sort order
                                    and reset to the default
    --format-sort-force             Force user specified sort order to have
                                    precedence over all fields, see "Sorting
                                    Formats" for more details (Alias: --S-force)
    --no-format-sort-force          Some fields have precedence over the user
                                    specified sort order (default)
    --video-multistreams            Allow multiple video streams to be merged
                                    into a single file
    --no-video-multistreams         Only one video stream is downloaded for each
                                    output file (default)
    --audio-multistreams            Allow multiple audio streams to be merged
                                    into a single file
    --no-audio-multistreams         Only one audio stream is downloaded for each
                                    output file (default)
    --prefer-free-formats           Prefer video formats with free containers
                                    over non-free ones of the same quality. Use
                                    with "-S ext" to strictly prefer free
                                    containers irrespective of quality
    --no-prefer-free-formats        Don't give any special preference to free
                                    containers (default)
    --check-formats                 Make sure formats are selected only from
                                    those that are actually downloadable
    --check-all-formats             Check all formats for whether they are
                                    actually downloadable
    --no-check-formats              Do not check that the formats are actually
                                    downloadable
    -F, --list-formats              List available formats of each video.
                                    Simulate unless --no-simulate is used
    --merge-output-format FORMAT    Containers that may be used when merging
                                    formats, separated by "/", e.g. "mp4/mkv".
                                    Ignored if no merge is required. (currently
                                    supported: avi, flv, mkv, mov, mp4, webm)

## Subtitle Options:
    --write-subs                    Write subtitle file
    --no-write-subs                 Do not write subtitle file (default)
    --write-auto-subs               Write automatically generated subtitle file
                                    (Alias: --write-automatic-subs)
    --no-write-auto-subs            Do not write auto-generated subtitles
                                    (default) (Alias: --no-write-automatic-subs)
    --list-subs                     List available subtitles of each video.
                                    Simulate unless --no-simulate is used
    --sub-format FORMAT             Subtitle format; accepts formats preference
                                    separated by "/", e.g. "srt" or "ass/srt/best"
    --sub-langs LANGS               Languages of the subtitles to download (can
                                    be regex) or "all" separated by commas, e.g.
                                    --sub-langs "en.*,ja" (where "en.*" is a
                                    regex pattern that matches "en" followed by
                                    0 or more of any character). You can prefix
                                    the language code with a "-" to exclude it
                                    from the requested languages, e.g. --sub-
                                    langs all,-live_chat. Use --list-subs for a
                                    list of available language tags

## Authentication Options:
    -u, --username USERNAME         Login with this account ID
    -p, --password PASSWORD         Account password. If this option is left
                                    out, yt-ai will ask interactively
    -2, --twofactor TWOFACTOR       Two-factor authentication code
    -n, --netrc                     Use .netrc authentication data
    --netrc-location PATH           Location of .netrc authentication data;
                                    either the path or its containing directory.
                                    Defaults to ~/.netrc
    --netrc-cmd NETRC_CMD           Command to execute to get the credentials
                                    for an extractor.
    --video-password PASSWORD       Video-specific password
    --ap-mso MSO                    Adobe Pass multiple-system operator (TV
                                    provider) identifier, use --ap-list-mso for
                                    a list of available MSOs
    --ap-username USERNAME          Multiple-system operator account login
    --ap-password PASSWORD          Multiple-system operator account password.
                                    If this option is left out, yt-ai will ask
                                    interactively
    --ap-list-mso                   List all supported multiple-system operators
    --client-certificate CERTFILE   Path to client certificate file in PEM
                                    format. May include the private key
    --client-certificate-key KEYFILE
                                    Path to private key file for client
                                    certificate
    --client-certificate-password PASSWORD
                                    Password for client certificate private key,
                                    if encrypted. If not provided, and the key
                                    is encrypted, yt-ai will ask interactively

## Post-Processing Options:
    -x, --extract-audio             Convert video files to audio-only files
                                    (requires ffmpeg and ffprobe)
    --audio-format FORMAT           Format to convert the audio to when -x is
                                    used. (currently supported: best (default),
                                    aac, alac, flac, m4a, mp3, opus, vorbis,
                                    wav). You can specify multiple rules using
                                    similar syntax as --remux-video
    --audio-quality QUALITY         Specify ffmpeg audio quality to use when
                                    converting the audio with -x. Insert a value
                                    between 0 (best) and 10 (worst) for VBR or a
                                    specific bitrate like 128K (default 5)
    --remux-video FORMAT            Remux the video into another container if
                                    necessary (currently supported: avi, flv,
                                    gif, mkv, mov, mp4, webm, aac, aiff, alac,
                                    flac, m4a, mka, mp3, ogg, opus, vorbis,
                                    wav). If the target container does not
                                    support the video/audio codec, remuxing will
                                    fail. You can specify multiple rules; e.g.
                                    "aac>m4a/mov>mp4/mkv" will remux aac to m4a,
                                    mov to mp4 and anything else to mkv
    --recode-video FORMAT           Re-encode the video into another format if
                                    necessary. The syntax and supported formats
                                    are the same as --remux-video
    --postprocessor-args NAME:ARGS  Give these arguments to the postprocessors.
                                    Specify the postprocessor/executable name
                                    and the arguments separated by a colon ":"
                                    to give the argument to the specified
                                    postprocessor/executable. Supported PP are:
                                    Merger, ModifyChapters, SplitChapters,
                                    ExtractAudio, VideoRemuxer, VideoConvertor,
                                    Metadata, EmbedSubtitle, EmbedThumbnail,
                                    SubtitlesConvertor, ThumbnailsConvertor,
                                    FixupStretched, FixupM4a, FixupM3u8,
                                    FixupTimestamp and FixupDuration. The
                                    supported executables are: AtomicParsley,
                                    FFmpeg and FFprobe. You can also specify
                                    "PP+EXE:ARGS" to give the arguments to the
                                    specified executable only when being used by
                                    the specified postprocessor. Additionally,
                                    for ffmpeg/ffprobe, "_i"/"_o" can be
                                    appended to the prefix optionally followed
                                    by a number to pass the argument before the
                                    specified input/output file, e.g. --ppa
                                    "Merger+ffmpeg_i1:-v quiet". You can use
                                    this option multiple times to give different
                                    arguments to different postprocessors.
                                    (Alias: --ppa)
    -k, --keep-video                Keep the intermediate video file on disk
                                    after post-processing
    --no-keep-video                 Delete the intermediate video file after
                                    post-processing (default)
    --post-overwrites               Overwrite post-processed files (default)
    --no-post-overwrites            Do not overwrite post-processed files
    --embed-subs                    Embed subtitles in the video (only for mp4,
                                    webm and mkv videos)
    --no-embed-subs                 Do not embed subtitles (default)
    --embed-thumbnail               Embed thumbnail in the video as cover art
    --no-embed-thumbnail            Do not embed thumbnail (default)
    --embed-metadata                Embed metadata to the video file. Also
                                    embeds chapters/infojson if present unless
                                    --no-embed-chapters/--no-embed-info-json are
                                    used (Alias: --add-metadata)
    --no-embed-metadata             Do not add metadata to file (default)
                                    (Alias: --no-add-metadata)
    --embed-chapters                Add chapter markers to the video file
                                    (Alias: --add-chapters)
    --no-embed-chapters             Do not add chapter markers (default) (Alias:
                                    --no-add-chapters)
    --embed-info-json               Embed the infojson as an attachment to
                                    mkv/mka video files
    --no-embed-info-json            Do not embed the infojson as an attachment
                                    to the video file
    --parse-metadata [WHEN:]FROM:TO
                                    Parse additional metadata like title/artist
                                    from other fields; see "MODIFYING METADATA"
                                    for details. Supported values of "WHEN" are
                                    the same as that of --use-postprocessor
                                    (default: pre_process)
    --replace-in-metadata [WHEN:]FIELDS REGEX REPLACE
                                    Replace text in a metadata field using the
                                    given regex. This option can be used
                                    multiple times. Supported values of "WHEN"
                                    are the same as that of --use-postprocessor
                                    (default: pre_process)
    --xattrs                        Write metadata to the video file's xattrs
                                    (using Dublin Core and XDG standards)
    --concat-playlist POLICY        Concatenate videos in a playlist. One of
                                    "never", "always", or "multi_video"
                                    (default; only when the videos form a single
                                    show). All the video files must have the
                                    same codecs and number of streams to be
                                    concatenable. The "pl_video:" prefix can be
                                    used with "--paths" and "--output" to set
                                    the output filename for the concatenated
                                    files. See "OUTPUT TEMPLATE" for details
    --fixup POLICY                  Automatically correct known faults of the
                                    file. One of never (do nothing), warn (only
                                    emit a warning), detect_or_warn (the
                                    default; fix the file if we can, warn
                                    otherwise), force (try fixing even if the
                                    file already exists)
    --ffmpeg-location PATH          Location of the ffmpeg binary; either the
                                    path to the binary or its containing directory
    --exec [WHEN:]CMD               Execute a command, optionally prefixed with
                                    when to execute it, separated by a ":".
                                    Supported values of "WHEN" are the same as
                                    that of --use-postprocessor (default:
                                    after_move). The same syntax as the output
                                    template can be used to pass any field as
                                    arguments to the command; however, for
                                    security reasons the only allowed
                                    conversions are: "i"/"d" (signed integer
                                    decimal), "f" (floating-point decimal) and
                                    "q" (shell-quoted). If no fields are passed,
                                    %(filepath,_filename|)q is appended to the
                                    end of the command. This option can be used
                                    multiple times
    --no-exec                       Remove any previously defined --exec
    --convert-subs FORMAT           Convert the subtitles to another format
                                    (currently supported: ass, lrc, srt, vtt).
                                    Use "--convert-subs none" to disable
                                    conversion (default) (Alias: --convert-
                                    subtitles)
    --convert-thumbnails FORMAT     Convert the thumbnails to another format
                                    (currently supported: jpg, png, webp). You
                                    can specify multiple rules using similar
                                    syntax as "--remux-video". Use "--convert-
                                    thumbnails none" to disable conversion
                                    (default)
    --split-chapters                Split video into multiple files based on
                                    internal chapters. The "chapter:" prefix can
                                    be used with "--paths" and "--output" to set
                                    the output filename for the split files. See
                                    "OUTPUT TEMPLATE" for details
    --no-split-chapters             Do not split video based on chapters (default)
    --remove-chapters REGEX         Remove chapters whose title matches the
                                    given regular expression. The syntax is the
                                    same as --download-sections. This option can
                                    be used multiple times
    --no-remove-chapters            Do not remove any chapters from the file
                                    (default)
    --force-keyframes-at-cuts       Force keyframes at cuts when
                                    downloading/splitting/removing sections.
                                    This is slow due to needing a re-encode, but
                                    the resulting video may have fewer artifacts
                                    around the cuts
    --no-force-keyframes-at-cuts    Do not force keyframes around the chapters
                                    when cutting/splitting (default)
    --use-postprocessor NAME[:ARGS]
                                    The (case-sensitive) name of plugin
                                    postprocessors to be enabled, and
                                    (optionally) arguments to be passed to it,
                                    separated by a colon ":". ARGS are a
                                    semicolon ";" delimited list of NAME=VALUE.
                                    The "when" argument determines when the
                                    postprocessor is invoked. It can be one of
                                    "pre_process" (after video extraction),
                                    "after_filter" (after video passes filter),
                                    "video" (after --format; before
                                    --print/--output), "before_dl" (before each
                                    video download), "post_process" (after each
                                    video download; default), "after_move"
                                    (after moving the video file to its final
                                    location), "after_video" (after downloading
                                    and processing all formats of a video), or
                                    "playlist" (at end of playlist). This option
                                    can be used multiple times to add different
                                    postprocessors

## SponsorBlock Options:
Make chapter entries for, or remove various segments (sponsor,
    introductions, etc.) from downloaded YouTube videos using the
    [SponsorBlock API](https://sponsor.ajay.app)

    --sponsorblock-mark CATS        SponsorBlock categories to create chapters
                                    for, separated by commas. Available
                                    categories are sponsor, intro, outro,
                                    selfpromo, preview, filler, interaction,
                                    music_offtopic, hook, poi_highlight,
                                    chapter, all and default (=all). You can
                                    prefix the category with a "-" to exclude
                                    it. See [1] for descriptions of the
                                    categories. E.g. --sponsorblock-mark
                                    all,-preview
                                    [1] https://wiki.sponsor.ajay.app/w/Segment_Categories
    --sponsorblock-remove CATS      SponsorBlock categories to be removed from
                                    the video file, separated by commas. If a
                                    category is present in both mark and remove,
                                    remove takes precedence. The syntax and
                                    available categories are the same as for
                                    --sponsorblock-mark except that "default"
                                    refers to "all,-filler" and poi_highlight,
                                    chapter are not available
    --sponsorblock-chapter-title TEMPLATE
                                    An output template for the title of the
                                    SponsorBlock chapters created by
                                    --sponsorblock-mark. The only available
                                    fields are start_time, end_time, category,
                                    categories, name, category_names. Defaults
                                    to "[SponsorBlock]: %(category_names)l"
    --no-sponsorblock               Disable both --sponsorblock-mark and
                                    --sponsorblock-remove
    --sponsorblock-api URL          SponsorBlock API location, defaults to
                                    https://sponsor.ajay.app

## Extractor Options:
    --extractor-retries RETRIES     Number of retries for known extractor errors
                                    (default is 3), or "infinite"
    --allow-dynamic-mpd             Process dynamic DASH manifests (default)
                                    (Alias: --no-ignore-dynamic-mpd)
    --ignore-dynamic-mpd            Do not process dynamic DASH manifests
                                    (Alias: --no-allow-dynamic-mpd)
    --hls-split-discontinuity       Split HLS playlists to different formats at
                                    discontinuities such as ad breaks
    --no-hls-split-discontinuity    Do not split HLS playlists into different
                                    formats at discontinuities such as ad breaks
                                    (default)
    --extractor-args IE_KEY:ARGS    Pass ARGS arguments to the IE_KEY extractor.
                                    See "EXTRACTOR ARGUMENTS" for details. You
                                    can use this option multiple times to give
                                    arguments for different extractors

## Preset Aliases:
Predefined aliases for convenience and ease of use. Note that future
    versions of yt-ai may add or adjust presets, but the existing preset
    names will not be changed or removed

    -t mp3                          -f 'ba[acodec^=mp3]/ba/b' -x --audio-format
                                    mp3

    -t aac                          -f
                                    'ba[acodec^=aac]/ba[acodec^=mp4a.40.]/ba/b'
                                    -x --audio-format aac

    -t mp4                          --merge-output-format mp4 --remux-video mp4
                                    -S vcodec:h264,lang,quality,res,fps,hdr:12,a
                                    codec:aac

    -t mkv                          --merge-output-format mkv --remux-video mkv

    -t sleep                        --sleep-subtitles 5 --sleep-requests 0.75
                                    --sleep-interval 10 --max-sleep-interval 20

# CONFIGURATION

You can configure yt-ai by placing any supported command line option in a configuration file. The configuration is loaded from the following locations:

1. **Main Configuration**:
    * The file given to `--config-locations`
1. **Portable Configuration**: (Recommended for portable installations)
    * If using a binary, `yt-ai.conf` in the same directory as the binary
    * If running from source-code, `yt-ai.conf` in the parent directory of `yt_dlp`
1. **Home Configuration**:
    * `yt-ai.conf` in the home path given to `-P`
    * If `-P` is not given, the current directory is searched
1. **User Configuration**:
    * `${XDG_CONFIG_HOME}/yt-ai.conf`
    * `${XDG_CONFIG_HOME}/yt-ai/config` (recommended on Linux/macOS)
    * `${XDG_CONFIG_HOME}/yt-ai/config.txt`
    * `${APPDATA}/yt-ai.conf`
    * `${APPDATA}/yt-ai/config` (recommended on Windows)
    * `${APPDATA}/yt-ai/config.txt`
    * `~/yt-ai.conf`
    * `~/yt-ai.conf.txt`
    * `~/.yt-ai/config`
    * `~/.yt-ai/config.txt`

    See also: [Notes about environment variables](#notes-about-environment-variables)
1. **System Configuration**:
    * `/etc/yt-ai.conf`
    * `/etc/yt-ai/config`
    * `/etc/yt-ai/config.txt`

E.g. with the following configuration file, yt-ai will always extract the audio, copy the mtime, use a proxy and save all videos under `YouTube` directory in your home directory:
```
# Lines starting with # are comments

# Always extract audio
-x

# Copy the mtime
--mtime

# Use this proxy
--proxy 127.0.0.1:3128

# Save all videos under YouTube directory in your home directory
-o ~/YouTube/%(title)s.%(ext)s
```

**Note**: Options in a configuration file are just the same options aka switches used in regular command line calls; thus there **must be no whitespace** after `-` or `--`, e.g. `-o` or `--proxy` but not `- o` or `-- proxy`. They must also be quoted when necessary, as if it were a UNIX shell.

You can use `--ignore-config` if you want to disable all configuration files for a particular yt-ai run. If `--ignore-config` is found inside any configuration file, no further configuration will be loaded. For example, having the option in the portable configuration file prevents loading of home, user, and system configurations. Additionally, (for backward compatibility) if `--ignore-config` is found inside the system configuration file, the user configuration is not loaded.

### Configuration file encoding

The configuration files are decoded according to the UTF BOM if present, and in the encoding from system locale otherwise.

If you want your file to be decoded differently, add `# coding: ENCODING` to the beginning of the file (e.g. `# coding: shift-jis`). There must be no characters before that, even spaces or BOM.

### Authentication with netrc

You may also want to configure automatic credentials storage for extractors that support authentication (by providing login and password with `--username` and `--password`) in order not to pass credentials as command line arguments on every yt-ai execution and prevent tracking plain text passwords in the shell command history. You can achieve this using a [`.netrc` file](https://stackoverflow.com/tags/.netrc/info) on a per-extractor basis. For that, you will need to create a `.netrc` file in `--netrc-location` and restrict permissions to read/write by only you:
```
touch ${HOME}/.netrc
chmod a-rwx,u+rw ${HOME}/.netrc
```
After that, you can add credentials for an extractor in the following format, where *extractor* is the name of the extractor in lowercase:
```
machine <extractor> login <username> password <password>
```
E.g.
```
machine youtube login myaccount@gmail.com password my_youtube_password
machine twitch login my_twitch_account_name password my_twitch_password
```
To activate authentication with the `.netrc` file you should pass `--netrc` to yt-ai or place it in the [configuration file](#configuration).

The default location of the .netrc file is `~` (see below).

As an alternative to using the `.netrc` file, which has the disadvantage of keeping your passwords in a plain text file, you can configure a custom shell command to provide the credentials for an extractor. This is done by providing the `--netrc-cmd` parameter, it shall output the credentials in the netrc format and return `0` on success, other values will be treated as an error. `{}` in the command will be replaced by the name of the extractor to make it possible to select the credentials for the right extractor.

E.g. To use an encrypted `.netrc` file stored as `.authinfo.gpg`
```
yt-ai --netrc-cmd 'gpg --decrypt ~/.authinfo.gpg' 'https://www.youtube.com/watch?v=YE7VzlLtp-4'
```


### Notes about environment variables
* Environment variables are normally specified as `${VARIABLE}`/`$VARIABLE` on UNIX and `%VARIABLE%` on Windows; but is always shown as `${VARIABLE}` in this documentation
* yt-ai also allows using UNIX-style variables on Windows for path-like options; e.g. `--output`, `--config-locations`
* If unset, `${XDG_CONFIG_HOME}` defaults to `~/.config` and `${XDG_CACHE_HOME}` to `~/.cache`
* On Windows, `~` points to `${HOME}` if present; or, `${USERPROFILE}` or `${HOMEDRIVE}${HOMEPATH}` otherwise
* On Windows, `${USERPROFILE}` generally points to `C:\Users\<user name>` and `${APPDATA}` to `${USERPROFILE}\AppData\Roaming`

# OUTPUT TEMPLATE

The `-o` option is used to indicate a template for the output file names while `-P` option is used to specify the path each type of file should be saved to.

<!-- MANPAGE: BEGIN EXCLUDED SECTION -->
**tl;dr:** [navigate me to examples](#output-template-examples).
<!-- MANPAGE: END EXCLUDED SECTION -->

The simplest usage of `-o` is not to set any template arguments when downloading a single file, like in `yt-ai -o funny_video.flv "https://some/video"` (hard-coding file extension like this is _not_ recommended and could break some post-processing).

It may however also contain special sequences that will be replaced when downloading each video. The special sequences may be formatted according to [Python string formatting operations](https://docs.python.org/3/library/stdtypes.html#printf-style-string-formatting), e.g. `%(NAME)s` or `%(NAME)05d`. To clarify, that is a percent symbol followed by a name in parentheses, followed by formatting operations.

The field names themselves (the part inside the parenthesis) can also have some special formatting:

1. **Object traversal**: The dictionaries and lists available in metadata can be traversed by using a dot `.` separator; e.g. `%(tags.0)s`, `%(subtitles.en.-1.ext)s`. You can do Python slicing with colon `:`; E.g. `%(id.3:7)s`, `%(id.6:2:-1)s`, `%(formats.:.format_id)s`. Curly braces `{}` can be used to build dictionaries with only specific keys; e.g. `%(formats.:.{format_id,height})#j`. An empty field name `%()s` refers to the entire infodict; e.g. `%(.{id,title})s`. Note that all the fields that become available using this method are not listed below. Use `-j` to see such fields

1. **Arithmetic**: Simple arithmetic can be done on numeric fields using `+`, `-` and `*`. E.g. `%(playlist_index+10)03d`, `%(n_entries+1-playlist_index)d`

1. **Date/time Formatting**: Date/time fields can be formatted according to [strftime formatting](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes) by specifying it separated from the field name using a `>`. E.g. `%(duration>%H-%M-%S)s`, `%(upload_date>%Y-%m-%d)s`, `%(epoch-3600>%H-%M-%S)s`

1. **Alternatives**: Alternate fields can be specified separated with a `,`. E.g. `%(release_date>%Y,upload_date>%Y|Unknown)s`

1. **Replacement**: A replacement value can be specified using a `&` separator according to the [`str.format` mini-language](https://docs.python.org/3/library/string.html#format-specification-mini-language). If the field is *not* empty, this replacement value will be used instead of the actual field content. This is done after alternate fields are considered; thus the replacement is used if *any* of the alternative fields is *not* empty. E.g. `%(chapters&has chapters|no chapters)s`, `%(title&TITLE={:>20}|NO TITLE)s`

1. **Default**: A literal default value can be specified for when the field is empty using a `|` separator. This overrides `--output-na-placeholder`. E.g. `%(uploader|Unknown)s`

1. **More Conversions**: In addition to the normal format types `diouxXeEfFgGcrs`, yt-ai additionally supports converting to `B` = **B**ytes, `j` = **j**son (flag `#` for pretty-printing, `+` for Unicode), `h` = HTML escaping, `l` = a comma-separated **l**ist (flag `#` for `\n` newline-separated), `q` = a string **q**uoted for the terminal (flag `#` to split a list into different arguments), `D` = add **D**ecimal suffixes (e.g. 10M) (flag `#` to use 1024 as factor), and `S` = **S**anitize as filename (flag `#` for restricted)

1. **Unicode normalization**: The format type `U` can be used for NFC [Unicode normalization](https://docs.python.org/3/library/unicodedata.html#unicodedata.normalize). The alternate form flag (`#`) changes the normalization to NFD and the conversion flag `+` can be used for NFKC/NFKD compatibility equivalence normalization. E.g. `%(title)+.100U` is NFKC

To summarize, the general syntax for a field is:
```
%(name[.keys][addition][>strf][,alternate][&replacement][|default])[flags][width][.precision][length]type
```

Additionally, you can set different output templates for the various metadata files separately from the general output template by specifying the type of file followed by the template separated by a colon `:`. The different file types supported are `subtitle`, `thumbnail`, `description`, `annotation` (deprecated), `infojson`, `link`, `pl_thumbnail`, `pl_description`, `pl_infojson`, `chapter`, `pl_video`. E.g. `-o "%(title)s.%(ext)s" -o "thumbnail:%(title)s/%(title)s.%(ext)s"` will put the thumbnails in a folder with the same name as the video. If any of the templates is empty, that type of file will not be written. E.g. `--write-thumbnail -o "thumbnail:"` will write thumbnails only for playlists and not for video.

<a id="outtmpl-postprocess-note"></a>

**Note**: Due to post-processing (i.e. merging etc.), the actual output filename might differ. Use `--print after_move:filepath` to get the name after all post-processing is complete.

The available fields are:

 - `id` (string): Video identifier
 - `title` (string): Video title
 - `fulltitle` (string): Video title ignoring live timestamp and generic title
 - `ext` (string): Video filename extension
 - `alt_title` (string): A secondary title of the video
 - `description` (string): The description of the video
 - `display_id` (string): An alternative identifier for the video
 - `uploader` (string): Full name of the video uploader
 - `uploader_id` (string): Nickname or id of the video uploader
 - `uploader_url` (string): URL to the video uploader's profile
 - `license` (string): License name the video is licensed under
 - `creators` (list): The creators of the video
 - `creator` (string): The creators of the video; comma-separated
 - `timestamp` (numeric): UNIX timestamp of the moment the video became available
 - `upload_date` (string): Video upload date in UTC (YYYYMMDD)
 - `release_timestamp` (numeric): UNIX timestamp of the moment the video was released
 - `release_date` (string): The date (YYYYMMDD) when the video was released in UTC
 - `release_year` (numeric): Year (YYYY) when the video or album was released
 - `modified_timestamp` (numeric): UNIX timestamp of the moment the video was last modified
 - `modified_date` (string): The date (YYYYMMDD) when the video was last modified in UTC
 - `channel` (string): Full name of the channel the video is uploaded on
 - `channel_id` (string): Id of the channel
 - `channel_url` (string): URL of the channel
 - `channel_follower_count` (numeric): Number of followers of the channel
 - `channel_is_verified` (boolean): Whether the channel is verified on the platform
 - `location` (string): Physical location where the video was filmed
 - `duration` (numeric): Length of the video in seconds
 - `duration_string` (string): Length of the video (HH:mm:ss)
 - `view_count` (numeric): How many users have watched the video on the platform
 - `concurrent_view_count` (numeric): How many users are currently watching the video on the platform.
 - `like_count` (numeric): Number of positive ratings of the video
 - `dislike_count` (numeric): Number of negative ratings of the video
 - `repost_count` (numeric): Number of reposts of the video
 - `average_rating` (numeric): Average rating given by users, the scale used depends on the webpage
 - `comment_count` (numeric): Number of comments on the video (For some extractors, comments are only downloaded at the end, and so this field cannot be used)
 - `save_count` (numeric): Number of times the video has been saved or bookmarked
 - `age_limit` (numeric): Age restriction for the video (years)
 - `live_status` (string): One of "not_live", "is_live", "is_upcoming", "was_live", "post_live" (was live, but VOD is not yet processed)
 - `is_live` (boolean): Whether this video is a live stream or a fixed-length video
 - `was_live` (boolean): Whether this video was originally a live stream
 - `playable_in_embed` (string): Whether this video is allowed to play in embedded players on other sites
 - `availability` (string): Whether the video is "private", "premium_only", "subscriber_only", "needs_auth", "unlisted" or "public"
 - `media_type` (string): The type of media as classified by the site, e.g. "episode", "clip", "trailer"
 - `start_time` (numeric): Time in seconds where the reproduction should start, as specified in the URL
 - `end_time` (numeric): Time in seconds where the reproduction should end, as specified in the URL
 - `extractor` (string): Name of the extractor
 - `extractor_key` (string): Key name of the extractor
 - `epoch` (numeric): Unix epoch of when the information extraction was completed
 - `autonumber` (numeric): Number that will be increased with each download, starting at `--autonumber-start`, padded with leading zeros to 5 digits
 - `video_autonumber` (numeric): Number that will be increased with each video
 - `n_entries` (numeric): Total number of extracted items in the playlist
 - `playlist_id` (string): Identifier of the playlist that contains the video
 - `playlist_title` (string): Name of the playlist that contains the video
 - `playlist` (string): `playlist_title` if available or else `playlist_id`
 - `playlist_count` (numeric): Total number of items in the playlist. May not be known if entire playlist is not extracted
 - `playlist_index` (numeric): Index of the video in the playlist padded with leading zeros according the final index
 - `playlist_autonumber` (numeric): Position of the video in the playlist download queue padded with leading zeros according to the total length of the playlist
 - `playlist_uploader` (string): Full name of the playlist uploader
 - `playlist_uploader_id` (string): Nickname or id of the playlist uploader
 - `playlist_channel` (string): Display name of the channel that uploaded the playlist
 - `playlist_channel_id` (string): Identifier of the channel that uploaded the playlist
 - `playlist_webpage_url` (string): URL of the playlist webpage
 - `webpage_url` (string): A URL to the video webpage which, if given to yt-ai, should yield the same result again
 - `webpage_url_basename` (string): The basename of the webpage URL
 - `webpage_url_domain` (string): The domain of the webpage URL
 - `original_url` (string): The URL given by the user (or the same as `webpage_url` for playlist entries)
 - `categories` (list): List of categories the video belongs to
 - `tags` (list): List of tags assigned to the video
 - `cast` (list): List of cast members

All the fields in [Filtering Formats](#filtering-formats) can also be used

Available for the video that belongs to some logical chapter or section:

 - `chapter` (string): Name or title of the chapter the video belongs to
 - `chapter_number` (numeric): Number of the chapter the video belongs to
 - `chapter_id` (string): Id of the chapter the video belongs to

Available for the video that is an episode of some series or program:

 - `series` (string): Title of the series or program the video episode belongs to
 - `series_id` (string): Id of the series or program the video episode belongs to
 - `season` (string): Title of the season the video episode belongs to
 - `season_number` (numeric): Number of the season the video episode belongs to
 - `season_id` (string): Id of the season the video episode belongs to
 - `episode` (string): Title of the video episode
 - `episode_number` (numeric): Number of the video episode within a season
 - `episode_id` (string): Id of the video episode

Available for the media that is a track or a part of a music album:

 - `track` (string): Title of the track
 - `track_number` (numeric): Number of the track within an album or a disc
 - `track_id` (string): Id of the track
 - `artists` (list): Artist(s) of the track
 - `artist` (string): Artist(s) of the track; comma-separated
 - `genres` (list): Genre(s) of the track
 - `genre` (string): Genre(s) of the track; comma-separated
 - `composers` (list): Composer(s) of the piece
 - `composer` (string): Composer(s) of the piece; comma-separated
 - `album` (string): Title of the album the track belongs to
 - `album_type` (string): Type of the album
 - `album_artists` (list): All artists appeared on the album
 - `album_artist` (string): All artists appeared on the album; comma-separated
 - `disc_number` (numeric): Number of the disc or other physical medium the track belongs to

Available only when using `--download-sections` and for `chapter:` prefix when using `--split-chapters` for videos with internal chapters:

 - `section_title` (string): Title of the chapter
 - `section_number` (numeric): Number of the chapter within the file
 - `section_start` (numeric): Start time of the chapter in seconds
 - `section_end` (numeric): End time of the chapter in seconds

Available only when used in `--print`:

 - `urls` (string): The URLs of all requested formats, one in each line
 - `filename` (string): Name of the video file. Note that the [actual filename may differ](#outtmpl-postprocess-note)
 - `formats_table` (table): The video format table as printed by `--list-formats`
 - `thumbnails_table` (table): The thumbnail format table as printed by `--list-thumbnails`
 - `subtitles_table` (table): The subtitle format table as printed by `--list-subs`
 - `automatic_captions_table` (table): The automatic subtitle format table as printed by `--list-subs`

 Available only after the video is downloaded (`post_process`/`after_move`):

 - `filepath`: Actual path of downloaded video file

Available only in `--sponsorblock-chapter-title`:

 - `start_time` (numeric): Start time of the chapter in seconds
 - `end_time` (numeric): End time of the chapter in seconds
 - `categories` (list): The [SponsorBlock categories](https://wiki.sponsor.ajay.app/w/Types#Category) the chapter belongs to
 - `category` (string): The smallest SponsorBlock category the chapter belongs to
 - `category_names` (list): Friendly names of the categories
 - `name` (string): Friendly name of the smallest category
 - `type` (string): The [SponsorBlock action type](https://wiki.sponsor.ajay.app/w/Types#Action_Type) of the chapter

Each aforementioned sequence when referenced in an output template will be replaced by the actual value corresponding to the sequence name. E.g. for `-o %(title)s-%(id)s.%(ext)s` and an mp4 video with title `yt-ai test video` and id `YE7VzlLtp-4`, this will result in a `yt-ai test video-YE7VzlLtp-4.mp4` file created in the current directory.

**Note**: Some of the sequences are not guaranteed to be present, since they depend on the metadata obtained by a particular extractor. Such sequences will be replaced with placeholder value provided with `--output-na-placeholder` (`NA` by default).

**Tip**: Look at the `-j` output to identify which fields are available for the particular URL

For numeric sequences, you can use [numeric related formatting](https://docs.python.org/3/library/stdtypes.html#printf-style-string-formatting); e.g. `%(view_count)05d` will result in a string with view count padded with zeros up to 5 characters, like in `00042`.

Output templates can also contain arbitrary hierarchical path, e.g. `-o "%(playlist)s/%(playlist_index)s - %(title)s.%(ext)s"` which will result in downloading each video in a directory corresponding to this path template. Any missing directory will be automatically created for you.

To use percent literals in an output template use `%%`. To output to stdout use `-o -`.

The current default template is `%(title)s [%(id)s].%(ext)s`.

In some cases, you don't want special characters such as 中, spaces, or &, such as when transferring the downloaded filename to a Windows system or the filename through an 8bit-unsafe channel. In these cases, add the `--restrict-filenames` flag to get a shorter title.

#### Output template examples

```bash
$ yt-ai --print filename -o "test video.%(ext)s" ptd1NN40vMw
test video.webm    # Literal name with correct extension

$ yt-ai --print filename -o "%(title)s.%(ext)s" ptd1NN40vMw
To'y!🤯😂🤦🏻‍♂️.webm    # All kinds of weird characters

$ yt-ai --print filename -o "%(title)s.%(ext)s" ptd1NN40vMw --restrict-filenames
To_y.webm    # Restricted file name

# Download YouTube playlist videos in separate directory indexed by video order in a playlist
$ yt-ai -o "%(playlist)s/%(playlist_index)s - %(title)s.%(ext)s" "https://www.youtube.com/playlist?list=PLwiyx1dc3P2JR9N8gQaQN_BCvlSlap7re"

# Download YouTube playlist videos in separate directories according to their uploaded year
$ yt-ai -o "%(upload_date>%Y)s/%(title)s.%(ext)s" "https://www.youtube.com/playlist?list=PLwiyx1dc3P2JR9N8gQaQN_BCvlSlap7re"

# Prefix playlist index with " - " separator, but only if it is available
$ yt-ai -o "%(playlist_index&{} - |)s%(title)s.%(ext)s" YE7VzlLtp-4 "https://www.youtube.com/user/TheLinuxFoundation/playlists"

# Download all playlists of YouTube channel/user keeping each playlist in separate directory:
$ yt-ai -o "%(uploader)s/%(playlist)s/%(playlist_index)s - %(title)s.%(ext)s" "https://www.youtube.com/user/TheLinuxFoundation/playlists"

# Download Udemy course keeping each chapter in separate directory under MyVideos directory in your home
$ yt-ai -u user -p password -P "~/MyVideos" -o "%(playlist)s/%(chapter_number)s - %(chapter)s/%(title)s.%(ext)s" "https://www.udemy.com/java-tutorial"

# Download entire series season keeping each series and each season in separate directory under C:/MyVideos
$ yt-ai -P "C:/MyVideos" -o "%(series)s/%(season_number)s - %(season)s/%(episode_number)s - %(episode)s.%(ext)s" "https://videomore.ru/kino_v_detalayah/5_sezon/367617"

# Download video as "C:\MyVideos\uploader\title.ext", subtitles as "C:\MyVideos\subs\uploader\title.ext"
# and put all temporary files in "C:\MyVideos\tmp"
$ yt-ai -P "C:/MyVideos" -P "temp:tmp" -P "subtitle:subs" -o "%(uploader)s/%(title)s.%(ext)s" YE7VzlLtp-4 --write-subs

# Download video as "C:\MyVideos\uploader\title.ext" and subtitles as "C:\MyVideos\uploader\subs\title.ext"
$ yt-ai -P "C:/MyVideos" -o "%(uploader)s/%(title)s.%(ext)s" -o "subtitle:%(uploader)s/subs/%(title)s.%(ext)s" YE7VzlLtp-4 --write-subs

# Stream the video being downloaded to stdout
$ yt-ai -o - YE7VzlLtp-4
```

# FORMAT SELECTION

By default, yt-ai tries to download the best available quality if you **don't** pass any options.
This is generally equivalent to using `-f bestvideo*+bestaudio/best`. However, if multiple audiostreams is enabled (`--audio-multistreams`), the default format changes to `-f bestvideo+bestaudio/best`. Similarly, if ffmpeg is unavailable, or if you use yt-ai to stream to `stdout` (`-o -`), the default becomes `-f best/bestvideo+bestaudio`.

**Deprecation warning**: Latest versions of yt-ai can stream multiple formats to the stdout simultaneously using ffmpeg. So, in future versions, the default for this will be set to `-f bv*+ba/b` similar to normal downloads. If you want to preserve the `-f b/bv+ba` setting, it is recommended to explicitly specify it in the configuration options.

The general syntax for format selection is `-f FORMAT` (or `--format FORMAT`) where `FORMAT` is a *selector expression*, i.e. an expression that describes format or formats you would like to download.

<!-- MANPAGE: BEGIN EXCLUDED SECTION -->
**tl;dr:** [navigate me to examples](#format-selection-examples).
<!-- MANPAGE: END EXCLUDED SECTION -->

The simplest case is requesting a specific format; e.g. with `-f 22` you can download the format with format code equal to 22. You can get the list of available format codes for particular video using `--list-formats` or `-F`. Note that these format codes are extractor specific.

You can also use a file extension (currently `3gp`, `aac`, `flv`, `m4a`, `mp3`, `mp4`, `ogg`, `wav`, `webm` are supported) to download the best quality format of a particular file extension served as a single file, e.g. `-f webm` will download the best quality format with the `webm` extension served as a single file.

You can use `-f -` to interactively provide the format selector *for each video*

You can also use special names to select particular edge case formats:

 - `all`: Select **all formats** separately
 - `mergeall`: Select and **merge all formats** (Must be used with `--audio-multistreams`, `--video-multistreams` or both)
 - `b*`, `best*`: Select the best quality format that **contains either** a video or an audio or both (i.e.; `vcodec!=none or acodec!=none`)
 - `b`, `best`: Select the best quality format that **contains both** video and audio. Equivalent to `best*[vcodec!=none][acodec!=none]`
 - `bv`, `bestvideo`: Select the best quality **video-only** format. Equivalent to `best*[acodec=none]`
 - `bv*`, `bestvideo*`: Select the best quality format that **contains video**. It may also contain audio. Equivalent to `best*[vcodec!=none]`
 - `ba`, `bestaudio`: Select the best quality **audio-only** format. Equivalent to `best*[vcodec=none]`
 - `ba*`, `bestaudio*`: Select the best quality format that **contains audio**. It may also contain video. Equivalent to `best*[acodec!=none]` ([Do not use!](https://github.com/yt-dlp/yt-dlp/issues/979#issuecomment-919629354))
 - `w*`, `worst*`: Select the worst quality format that contains either a video or an audio
 - `w`, `worst`: Select the worst quality format that contains both video and audio. Equivalent to `worst*[vcodec!=none][acodec!=none]`
 - `wv`, `worstvideo`: Select the worst quality video-only format. Equivalent to `worst*[acodec=none]`
 - `wv*`, `worstvideo*`: Select the worst quality format that contains video. It may also contain audio. Equivalent to `worst*[vcodec!=none]`
 - `wa`, `worstaudio`: Select the worst quality audio-only format. Equivalent to `worst*[vcodec=none]`
 - `wa*`, `worstaudio*`: Select the worst quality format that contains audio. It may also contain video. Equivalent to `worst*[acodec!=none]`

For example, to download the worst quality video-only format you can use `-f worstvideo`. It is, however, recommended not to use `worst` and related options. When your format selector is `worst`, the format which is worst in all respects is selected. Most of the time, what you actually want is the video with the smallest filesize instead. So it is generally better to use `-S +size` or more rigorously, `-S +size,+br,+res,+fps` instead of `-f worst`. See [Sorting Formats](#sorting-formats) for more details.

You can select the n'th best format of a type by using `best<type>.<n>`. For example, `best.2` will select the 2nd best combined format. Similarly, `bv*.3` will select the 3rd best format that contains a video stream.

If you want to download multiple videos, and they don't have the same formats available, you can specify the order of preference using slashes. Note that formats on the left hand side are preferred; e.g. `-f 22/17/18` will download format 22 if it's available, otherwise it will download format 17 if it's available, otherwise it will download format 18 if it's available, otherwise it will complain that no suitable formats are available for download.

If you want to download several formats of the same video use a comma as a separator, e.g. `-f 22,17,18` will download all these three formats, of course if they are available. Or a more sophisticated example combined with the precedence feature: `-f 136/137/mp4/bestvideo,140/m4a/bestaudio`.

You can merge the video and audio of multiple formats into a single file using `-f <format1>+<format2>+...` (requires ffmpeg installed); e.g. `-f bestvideo+bestaudio` will download the best video-only format, the best audio-only format and mux them together with ffmpeg.

**Deprecation warning**: Since the *below* described behavior is complex and counter-intuitive, this will be removed and multistreams will be enabled by default in the future. A new operator will be instead added to limit formats to single audio/video

Unless `--video-multistreams` is used, all formats with a video stream except the first one are ignored. Similarly, unless `--audio-multistreams` is used, all formats with an audio stream except the first one are ignored. E.g. `-f bestvideo+best+bestaudio --video-multistreams --audio-multistreams` will download and merge all 3 given formats. The resulting file will have 2 video streams and 2 audio streams. But `-f bestvideo+best+bestaudio --no-video-multistreams` will download and merge only `bestvideo` and `bestaudio`. `best` is ignored since another format containing a video stream (`bestvideo`) has already been selected. The order of the formats is therefore important. `-f best+bestaudio --no-audio-multistreams` will download only `best` while `-f bestaudio+best --no-audio-multistreams` will ignore `best` and download only `bestaudio`.

## Filtering Formats

You can also filter the video formats by putting a condition in brackets, as in `-f "best[height=720]"` (or `-f "[filesize>10M]"` since filters without a selector are interpreted as `best`).

The following numeric meta fields can be used with comparisons `<`, `<=`, `>`, `>=`, `=` (equals), `!=` (not equals):

 - `filesize`: The number of bytes, if known in advance
 - `filesize_approx`: An estimate for the number of bytes
 - `width`: Width of the video, if known
 - `height`: Height of the video, if known
 - `aspect_ratio`: Aspect ratio of the video, if known
 - `tbr`: Average bitrate of audio and video in [kbps](## "1000 bits/sec")
 - `abr`: Average audio bitrate in [kbps](## "1000 bits/sec")
 - `vbr`: Average video bitrate in [kbps](## "1000 bits/sec")
 - `asr`: Audio sampling rate in Hertz
 - `fps`: Frame rate
 - `audio_channels`: The number of audio channels
 - `stretched_ratio`: `width:height` of the video's pixels, if not square

Also filtering work for comparisons `=` (equals), `^=` (starts with), `$=` (ends with), `*=` (contains), `~=` (matches regex) and following string meta fields:

 - `url`: Video URL
 - `ext`: File extension
 - `acodec`: Name of the audio codec in use
 - `vcodec`: Name of the video codec in use
 - `container`: Name of the container format
 - `protocol`: The protocol that will be used for the actual download, lower-case (`http`, `https`, `rtmp`, `rtmpe`, `f4m`, `ism`, `http_dash_segments`, `m3u8`, or `m3u8_native`)
 - `language`: Language code
 - `dynamic_range`: The dynamic range of the video
 - `format_id`: A short description of the format
 - `format`: A human-readable description of the format
 - `format_note`: Additional info about the format
 - `resolution`: Textual description of width and height

Any string comparison may be prefixed with negation `!` in order to produce an opposite comparison, e.g. `!*=` (does not contain). The comparand of a string comparison needs to be quoted with either double or single quotes if it contains spaces or special characters other than `._-`.

**Note**: None of the aforementioned meta fields are guaranteed to be present since this solely depends on the metadata obtained by the particular extractor, i.e. the metadata offered by the website. Any other field made available by the extractor can also be used for filtering.

Formats for which the value is not known are excluded unless you put a question mark (`?`) after the operator. You can combine format filters, so `-f "bv[height<=?720][tbr>500]"` selects up to 720p videos (or videos where the height is not known) with a bitrate greater than 500 kbps. You can also use the filters with `all` to download all formats that satisfy the filter, e.g. `-f "all[vcodec=none]"` selects all audio-only formats.

Format selectors can also be grouped using parentheses; e.g. `-f "(mp4,webm)[height<480]"` will download the best pre-merged mp4 and webm formats with a height lower than 480.

## Sorting Formats

You can change the criteria for being considered the `best` by using `-S` (`--format-sort`). The general format for this is `--format-sort field1,field2...`.

The available fields are:

 - `hasvid`: Gives priority to formats that have a video stream
 - `hasaud`: Gives priority to formats that have an audio stream
 - `ie_pref`: The format preference
 - `lang`: The language preference as determined by the extractor (e.g. original language preferred over audio description)
 - `quality`: The quality of the format
 - `source`: The preference of the source
 - `proto`: Protocol used for download (`https`/`ftps` > `http`/`ftp` > `m3u8_native`/`m3u8` > `http_dash_segments`> `websocket_frag` > `f4f`/`f4m`)
 - `vcodec`: Video Codec (`av01` > `vp9.2` > `vp9` > `h265` > `h264` > `vp8` > `h263` > `theora` > other)
 - `acodec`: Audio Codec (`flac`/`alac` > `wav`/`aiff` > `opus` > `vorbis` > `aac` > `mp4a` > `mp3` > `ac4` > `eac3` > `ac3` > `dts` > other)
 - `codec`: Equivalent to `vcodec,acodec`
 - `vext`: Video Extension (`mp4` > `mov` > `webm` > `flv` > other). If `--prefer-free-formats` is used, `webm` is preferred.
 - `aext`: Audio Extension (`m4a` > `aac` > `mp3` > `ogg` > `opus` > `webm` > other). If `--prefer-free-formats` is used, the order changes to `ogg` > `opus` > `webm` > `mp3` > `m4a` > `aac`
 - `ext`: Equivalent to `vext,aext`
 - `filesize`: Exact filesize, if known in advance
 - `fs_approx`: Approximate filesize
 - `size`: Exact filesize if available, otherwise approximate filesize
 - `height`: Height of video
 - `width`: Width of video
 - `res`: Video resolution, calculated as the smallest dimension.
 - `fps`: Framerate of video
 - `hdr`: The dynamic range of the video (`DV` > `HDR12` > `HDR10+` > `HDR10` > `HLG` > `SDR`)
 - `channels`: The number of audio channels
 - `tbr`: Total average bitrate in [kbps](## "1000 bits/sec")
 - `vbr`: Average video bitrate in [kbps](## "1000 bits/sec")
 - `abr`: Average audio bitrate in [kbps](## "1000 bits/sec")
 - `br`: Average bitrate in [kbps](## "1000 bits/sec"), `tbr`/`vbr`/`abr`
 - `asr`: Audio sample rate in Hz

**Deprecation warning**: Many of these fields have (currently undocumented) aliases, that may be removed in a future version. It is recommended to use only the documented field names.

All fields, unless specified otherwise, are sorted in descending order. To reverse this, prefix the field with a `+`. E.g. `+res` prefers format with the smallest resolution. Additionally, you can suffix a preferred value for the fields, separated by a `:`. E.g. `res:720` prefers larger videos, but no larger than 720p and the smallest video if there are no videos less than 720p. For `codec` and `ext`, you can provide two preferred values, the first for video and the second for audio. E.g. `+codec:avc:m4a` (equivalent to `+vcodec:avc,+acodec:m4a`) sets the video codec preference to `h264` > `h265` > `vp9` > `vp9.2` > `av01` > `vp8` > `h263` > `theora` and audio codec preference to `mp4a` > `aac` > `vorbis` > `opus` > `mp3` > `ac3` > `dts`. You can also make the sorting prefer the nearest values to the provided by using `~` as the delimiter. E.g. `filesize~1G` prefers the format with filesize closest to 1 GiB.

The fields `hasvid` and `ie_pref` are always given highest priority in sorting, irrespective of the user-defined order. This behavior can be changed by using `--format-sort-force`. Apart from these, the default order used is: `lang,quality,res,fps,hdr:12,vcodec,channels,acodec,size,br,asr,proto,ext,hasaud,source,id`. The extractors may override this default order, but they cannot override the user-provided order.

Note that the default for hdr is `hdr:12`; i.e. Dolby Vision is not preferred. This choice was made since DV formats are not yet fully compatible with most devices. This may be changed in the future.

If your format selector is `worst`, the last item is selected after sorting. This means it will select the format that is worst in all respects. Most of the time, what you actually want is the video with the smallest filesize instead. So it is generally better to use `-f best -S +size,+br,+res,+fps`.

If you use the `-S`/`--format-sort` option multiple times, each subsequent sorting argument will be prepended to the previous one, and only the highest priority entry of any duplicated field will be preserved. E.g. `-S proto -S res` is equivalent to `-S res,proto`, and `-S res:720,fps -S vcodec,res:1080` is equivalent to `-S vcodec,res:1080,fps`. You can use `--format-sort-reset` to disregard any previously passed `-S`/`--format-sort` arguments and reset to the default order.

**Tip**: You can use the `-v -F` to see how the formats have been sorted (worst to best).

## Format Selection examples

```bash
# Download and merge the best video-only format and the best audio-only format,
# or download the best combined format if video-only format is not available
$ yt-ai -f "bv+ba/b"

# Download best format that contains video,
# and if it doesn't already have an audio stream, merge it with best audio-only format
$ yt-ai -f "bv*+ba/b"

# Same as above
$ yt-ai

# Download the best video-only format and the best audio-only format without merging them
# For this case, an output template should be used since
# by default, bestvideo and bestaudio will have the same file name.
$ yt-ai -f "bv,ba" -o "%(title)s.f%(format_id)s.%(ext)s"

# Download and merge the best format that has a video stream,
# and all audio-only formats into one file
$ yt-ai -f "bv*+mergeall[vcodec=none]" --audio-multistreams

# Download and merge the best format that has a video stream,
# and the best 2 audio-only formats into one file
$ yt-ai -f "bv*+ba+ba.2" --audio-multistreams


# The following examples show the old method (without -S) of format selection
# and how to use -S to achieve a similar but (generally) better result

# Download the worst video available (old method)
$ yt-ai -f "wv*+wa/w"

# Download the best video available but with the smallest resolution
$ yt-ai -S "+res"

# Download the smallest video available
$ yt-ai -S "+size,+br"



# Download the best mp4 video available, or the best video if no mp4 available
$ yt-ai -f "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4] / bv*+ba/b"

# Download the best video with the best extension
# (For video, mp4 > mov > webm > flv. For audio, m4a > aac > mp3 ...)
$ yt-ai -S "ext"



# Download the best video available but no better than 480p,
# or the worst video if there is no video under 480p
$ yt-ai -f "bv*[height<=480]+ba/b[height<=480] / wv*+ba/w"

# Download the best video available with the largest height but no better than 480p,
# or the best video with the smallest resolution if there is no video under 480p
$ yt-ai -S "height:480"

# Download the best video available with the largest resolution but no better than 480p,
# or the best video with the smallest resolution if there is no video under 480p
# Resolution is determined by using the smallest dimension.
# So this works correctly for vertical videos as well
$ yt-ai -S "res:480"



# Download the best video (that also has audio) but no bigger than 50 MB,
# or the worst video (that also has audio) if there is no video under 50 MB
$ yt-ai -f "b[filesize<50M] / w"

# Download the largest video (that also has audio) but no bigger than 50 MB,
# or the smallest video (that also has audio) if there is no video under 50 MB
$ yt-ai -f "b" -S "filesize:50M"

# Download the best video (that also has audio) that is closest in size to 50 MB
$ yt-ai -f "b" -S "filesize~50M"



# Download best video available via direct link over HTTP/HTTPS protocol,
# or the best video available via any protocol if there is no such video
$ yt-ai -f "(bv*+ba/b)[protocol^=http][protocol!*=dash] / (bv*+ba/b)"

# Download best video available via the best protocol
# (https/ftps > http/ftp > m3u8_native > m3u8 > http_dash_segments ...)
$ yt-ai -S "proto"



# Download the best video with either h264 or h265 codec,
# or the best video if there is no such video
$ yt-ai -f "(bv*[vcodec~='^((he|a)vc|h26[45])']+ba) / (bv*+ba/b)"

# Download the best video with best codec no better than h264,
# or the best video with worst codec if there is no such video
$ yt-ai -S "codec:h264"

# Download the best video with worst codec no worse than h264,
# or the best video with best codec if there is no such video
$ yt-ai -S "+codec:h264"



# More complex examples

# Download the best video no better than 720p preferring framerate greater than 30,
# or the worst video (still preferring framerate greater than 30) if there is no such video
$ yt-ai -f "((bv*[fps>30]/bv*)[height<=720]/(wv*[fps>30]/wv*)) + ba / (b[fps>30]/b)[height<=720]/(w[fps>30]/w)"

# Download the video with the largest resolution no better than 720p,
# or the video with the smallest resolution available if there is no such video,
# preferring larger framerate for formats with the same resolution
$ yt-ai -S "res:720,fps"



# Download the video with smallest resolution no worse than 480p,
# or the video with the largest resolution available if there is no such video,
# preferring better codec and then larger total bitrate for the same resolution
$ yt-ai -S "+res:480,codec,br"
```

# MODIFYING METADATA

The metadata obtained by the extractors can be modified by using `--parse-metadata` and `--replace-in-metadata`

`--replace-in-metadata FIELDS REGEX REPLACE` is used to replace text in any metadata field using [Python regular expression](https://docs.python.org/3/library/re.html#regular-expression-syntax). [Backreferences](https://docs.python.org/3/library/re.html?highlight=backreferences#re.sub) can be used in the replace string for advanced use.

The general syntax of `--parse-metadata FROM:TO` is to give the name of a field or an [output template](#output-template) to extract data from, and the format to interpret it as, separated by a colon `:`. Either a [Python regular expression](https://docs.python.org/3/library/re.html#regular-expression-syntax) with named capture groups, a single field name, or a similar syntax to the [output template](#output-template) (only `%(field)s` formatting is supported) can be used for `TO`. The option can be used multiple times to parse and modify various fields.

Note that these options preserve their relative order, allowing replacements to be made in parsed fields and vice versa. Also, any field thus created can be used in the [output template](#output-template) and will also affect the media file's metadata added when using `--embed-metadata`.

This option also has a few special uses:

* You can download an additional URL based on the metadata of the currently downloaded video. To do this, set the field `additional_urls` to the URL that you want to download. E.g. `--parse-metadata "description:(?P<additional_urls>https?://www\.vimeo\.com/\d+)"` will download the first vimeo video found in the description

* You can use this to change the metadata that is embedded in the media file. To do this, set the value of the corresponding field with a `meta_` prefix. For example, any value you set to `meta_description` field will be added to the `description` field in the file - you can use this to set a different "description" and "synopsis". To modify the metadata of individual streams, use the `meta<n>_` prefix (e.g. `meta1_language`). Any value set to the `meta_` field will overwrite all default values.

**Note**: Metadata modification happens before format selection, post-extraction and other post-processing operations. Some fields may be added or changed during these steps, overriding your changes.

For reference, these are the fields yt-ai adds by default to the file metadata:

Metadata fields            | From
:--------------------------|:------------------------------------------------
`title`                    | `track` or `title`
`date`                     | `upload_date`
`description`,  `synopsis` | `description`
`purl`, `comment`          | `webpage_url`
`track`                    | `track_number`
`artist`                   | `artist`, `artists`, `creator`, `creators`, `uploader` or `uploader_id`
`composer`                 | `composer` or `composers`
`genre`                    | `genre`, `genres`, `categories` or `tags`
`album`                    | `album` or `series`
`album_artist`             | `album_artist` or `album_artists`
`disc`                     | `disc_number`
`show`                     | `series`
`season_number`            | `season_number`
`episode_id`               | `episode` or `episode_id`
`episode_sort`             | `episode_number`
`language` of each stream  | the format's `language`

**Note**: The file format may not support some of these fields


## Modifying metadata examples

```bash
# Interpret the title as "Artist - Title"
$ yt-ai --parse-metadata "title:%(artist)s - %(title)s"

# Regex example
$ yt-ai --parse-metadata "description:Artist - (?P<artist>.+)"

# Copy the episode field to the title field (with FROM and TO as single fields)
$ yt-ai --parse-metadata "episode:title"

# Set title as "Series name S01E05"
$ yt-ai --parse-metadata "%(series)s S%(season_number)02dE%(episode_number)02d:%(title)s"

# Prioritize uploader as the "artist" field in video metadata
$ yt-ai --parse-metadata "%(uploader|)s:%(meta_artist)s" --embed-metadata

# Set "comment" field in video metadata using description instead of webpage_url,
# handling multiple lines correctly
$ yt-ai --parse-metadata "description:(?s)(?P<meta_comment>.+)" --embed-metadata

# Do not set any "synopsis" in the video metadata
$ yt-ai --parse-metadata ":(?P<meta_synopsis>)"

# Remove "formats" field from the infojson by setting it to an empty string
$ yt-ai --parse-metadata "video::(?P<formats>)" --write-info-json

# Replace all spaces and "_" in title and uploader with a `-`
$ yt-ai --replace-in-metadata "title,uploader" "[ _]" "-"

```

# EXTRACTOR ARGUMENTS

Some extractors accept additional arguments which can be passed using `--extractor-args KEY:ARGS`. `ARGS` is a `;` (semicolon) separated string of `ARG=VAL1,VAL2`. E.g. `--extractor-args "youtube:player-client=tv,mweb;formats=incomplete" --extractor-args "twitter:api=syndication"`

Note: In CLI, `ARG` can use `-` instead of `_`; e.g. `youtube:player-client"` becomes `youtube:player_client"`

The following extractors use this feature:

#### youtube
* `lang`: Prefer translated metadata (`title`, `description` etc) of this language code (case-sensitive). By default, the video primary language metadata is preferred, with a fallback to `en` translated. See [youtube/_base.py](https://github.com/CrimsonGlory/yt-ai/blob/415b4c9f955b1a0391204bd24a7132590e7b3bdb/yt_dlp/extractor/youtube/_base.py#L402-L409) for the list of supported content language codes
* `skip`: One or more of `hls`, `dash` or `translated_subs` to skip extraction of the m3u8 manifests, dash manifests and [auto-translated subtitles](https://github.com/yt-dlp/yt-dlp/issues/4090#issuecomment-1158102032) respectively
* `player_client`: Clients to extract video data from. The currently available clients are `web`, `web_safari`, `web_embedded`, `web_music`, `web_creator`, `mweb`, `ios`, `visionos`, `android`, `android_vr`, `tv`, `tv_downgraded`, and `tv_simply`. By default, `visionos,web` is used. If no JavaScript runtime/engine is available, then `web` is omitted. If logged-in cookies are passed to yt-ai, then `web_embedded,tv_downgraded,web` is used for free accounts and `web_creator,tv_downgraded,web` is used for premium accounts. The `web_music` client is added for `music.youtube.com` URLs when logged-in cookies are used. The `web_embedded` client is added for age-restricted videos but only successfully works around the age-restriction sometimes (e.g. if the video is embeddable). The `tv_downgraded` and `web_embedded` clients may be added as a fallback if `android_vr` or `visionos` is unable to access a video. The `web_creator` client is added for age-restricted videos if account age-verification is required. Some clients, such as `web_creator` and `web_music`, require a `po_token` for their formats to be downloadable. Some clients, such as `web_creator`, will only work with authentication. Not all clients support authentication via cookies. You can use `default` for the default clients, or you can use `all` for all clients (not recommended). You can prefix a client with `-` to exclude it, e.g. `youtube:player_client=default,-web`
* `player_skip`: Skip some network requests that are generally needed for robust extraction. One or more of `configs` (skip client configs), `webpage` (skip initial webpage), `js` (skip js player), `initial_data` (skip initial data/next ep request). While these options can help reduce the number of requests needed or avoid some rate-limiting, they could cause issues such as missing formats or metadata.  See [#860](https://github.com/yt-dlp/yt-dlp/pull/860) and [#12826](https://github.com/yt-dlp/yt-dlp/issues/12826) for more details
* `webpage_skip`: Skip extraction of embedded webpage data. One or both of `player_response`, `initial_data`. These options are for testing purposes and don't skip any network requests. Neither is skipped by default; however, if a `player_js_version` value other than `actual` is used, then `webpage_skip=player_response` is implied
* `webpage_client`: Client to use for the video webpage request. One of `web` (default) or `web_safari`
* `player_params`: YouTube player parameters to use for player requests. Will overwrite any default ones set by yt-ai.
* `player_js_variant`: The player javascript variant to use for n/sig deciphering. The known variants are: `main`, `tcc`, `tce`, `es5`, `es6`, `es6_tcc`, `es6_tce`, `tv`, `tv_es6`, `phone`, `house`. The default is `main`, and the others are for debugging purposes. You can use `actual` to go with what is prescribed by the site
* `player_js_version`: The player javascript version to use for n/sig deciphering, in the format of `signature_timestamp@hash` (e.g. `20348@0004de42`). The default is to use what is prescribed by the site, and can be selected with `actual`. Using any other value will imply `webpage_skip=player_response`
* `comment_sort`: `top` or `new` (default) - choose comment sorting mode (on YouTube's side)
* `max_comments`: Limit the amount of comments to gather. Comma-separated list of integers representing `max-comments,max-parents,max-replies,max-replies-per-thread,max-depth`. Default is `all,all,all,all,all`
    * A `max-depth` value of `1` will discard all replies, regardless of the `max-replies` or `max-replies-per-thread` values given
    * E.g. `all,all,1000,10,2` will get a maximum of 1000 replies total, with up to 10 replies per thread, and only 2 levels of depth (i.e. top-level comments plus their immediate replies). `1000,all,100` will get a maximum of 1000 comments, with a maximum of 100 replies total
* `formats`: Change the types of formats to return. `dashy` (convert HTTP to DASH), `duplicate` (identical content but different URLs or protocol; includes `dashy`), `incomplete` (cannot be downloaded completely - live and post-live dash, post-live m3u8, and live adaptive https without --live-from-start), `missing_pot` (include formats that require a PO Token but are missing one)
* `innertube_host`: Innertube API host to use for all API requests; e.g. `studio.youtube.com`, `youtubei.googleapis.com`. Note that cookies exported from one subdomain will not work on others
* `innertube_key`: Innertube API key to use for all API requests. By default, no API key is used
* `raise_incomplete_data`: `Incomplete Data Received` raises an error instead of reporting a warning
* `data_sync_id`: Overrides the account Data Sync ID used in Innertube API requests. This may be needed if you are using an account with `youtube:player_skip=webpage,configs` or `youtubetab:skip=webpage`
* `visitor_data`: Overrides the Visitor Data used in Innertube API requests. This should be used with `player_skip=webpage,configs` and without cookies. Note: this may have adverse effects if used improperly. If a session from a browser is wanted, you should pass cookies instead (which contain the Visitor ID)
* `po_token`:  Proof of Origin (PO) Token(s) to use. Comma-separated list of PO Tokens in the format `CLIENT.CONTEXT+PO_TOKEN`, e.g. `youtube:po_token=web.gvs+XXX,web.player=XXX,web_safari.gvs+YYY`. Context can be any of `gvs` (Google Video Server URLs), `player` (Innertube player request) or `subs` (Subtitles)
* `pot_trace`: Enable debug logging for PO Token fetching. Either `true` or `false` (default)
* `fetch_pot`: Policy to use for fetching a PO Token from providers. One of `always` (always try fetch a PO Token regardless if the client requires one for the given context), `never` (never fetch a PO Token), or `auto` (default; only fetch a PO Token if the client requires one for the given context)
* `jsc_trace`: Enable debug logging for JS Challenge fetching. Either `true` or `false` (default)
* `use_ad_playback_context`: Skip preroll ads to eliminate the mandatory wait period before download. Do NOT use this when passing premium account cookies to yt-ai, as it will result in a loss of premium formats. Only effective with the `mweb` and `web_music` player clients. Either `true` or `false` (default)

#### youtube-ejs
* `jitless`: Run supported Javascript engines in JIT-less mode. Supported runtimes are `deno`, `node` and `bun`. Provides better security at the cost of performance/speed. Do note that `node` and `bun` are still considered insecure. Either `true` or `false` (default)

#### youtubepot-webpo
* `bind_to_visitor_id`: Whether to use the Visitor ID instead of Visitor Data for caching WebPO tokens. Either `true` (default) or `false`

#### youtubetab (YouTube playlists, channels, feeds, etc.)
* `skip`: One or more of `webpage` (skip initial webpage download), `authcheck` (allow the download of playlists requiring authentication when no initial webpage is downloaded. This may cause unwanted behavior, see [#1122](https://github.com/yt-dlp/yt-dlp/pull/1122) for more details)
* `approximate_date`: Extract approximate `upload_date` and `timestamp` in flat-playlist. This may cause date-based filters to be slightly off

#### generic
* `fragment_query`: Passthrough any query in mpd/m3u8 manifest URLs to their fragments if no value is provided, or else apply the query string given as `fragment_query=VALUE`. Note that if the stream has an HLS AES-128 key, then the query parameters will be passed to the key URI as well, unless the `key_query` extractor-arg is passed, or unless an external key URI is provided via the `hls_key` extractor-arg. Does not apply to ffmpeg
* `variant_query`: Passthrough the master m3u8 URL query to its variant playlist URLs if no value is provided, or else apply the query string given as `variant_query=VALUE`
* `key_query`: Passthrough the master m3u8 URL query to its HLS AES-128 decryption key URI if no value is provided, or else apply the query string given as `key_query=VALUE`. Note that this will have no effect if the key URI is provided via the `hls_key` extractor-arg. Does not apply to ffmpeg
* `hls_key`: An HLS AES-128 key URI *or* key (as hex), and optionally the IV (as hex), in the form of `(URI|KEY)[,IV]`; e.g. `generic:hls_key=ABCDEF1234567980,0xFEDCBA0987654321`. Passing any of these values will force usage of the native HLS downloader and override the corresponding values found in the m3u8 playlist
* `is_live`: Bypass live HLS detection and manually set `live_status` - a value of `false` will set `not_live`, any other value (or no value) will set `is_live`
* `impersonate`: Target(s) to try and impersonate with the initial webpage request; e.g. `generic:impersonate=safari,chrome-110`. Use `generic:impersonate` to impersonate any available target, and use `generic:impersonate=false` to disable impersonation (default)

#### vikichannel
* `video_types`: Types of videos to download - one or more of `episodes`, `movies`, `clips`, `trailers`

#### youtubewebarchive
* `check_all`: Try to check more at the cost of more requests. One or more of `thumbnails`, `captures`

#### gamejolt
* `comment_sort`: `hot` (default), `you` (cookies needed), `top`, `new` - choose comment sorting mode (on GameJolt's side)

#### hotstar
* `res`: resolution to ignore - one or more of `sd`, `hd`, `fhd`
* `vcodec`: vcodec to ignore - one or more of `h264`, `h265`, `dvh265`
* `dr`: dynamic range to ignore - one or more of `sdr`, `hdr10`, `dv`

#### instagram
* `app_id`: The value of the `X-IG-App-ID` header used for API requests. Can be the actual ID number, `ios`, or `web` (default)

#### niconicochannelplus
* `max_comments`: Maximum number of comments to extract - default is `120`

#### tiktok
* `api_hostname`: Hostname to use for mobile API calls, e.g. `api22-normal-c-alisg.tiktokv.com`
* `app_name`: Default app name to use with mobile API calls, e.g. `trill`
* `app_version`: Default app version to use with mobile API calls - should be set along with `manifest_app_version`, e.g. `34.1.2`
* `manifest_app_version`: Default numeric app version to use with mobile API calls, e.g. `2023401020`
* `aid`: Default app ID to use with mobile API calls, e.g. `1180`
* `app_info`: Enable mobile API extraction with one or more app info strings in the format of `<iid>/[app_name]/[app_version]/[manifest_app_version]/[aid]`, where `iid` is the unique app install ID. `iid` is the only required value; all other values and their `/` separators can be omitted, e.g. `tiktok:app_info=1234567890123456789` or `tiktok:app_info=123,456/trill///1180,789//34.0.1/340001`
* `device_id`: Enable mobile API extraction with a genuine device ID to be used with mobile API calls. Default is a random 19-digit string

#### rokfinchannel
* `tab`: Which tab to download - one of `new`, `top`, `videos`, `podcasts`, `streams`, `stacks`

#### twitter
* `api`: Select one of `graphql` (default), `legacy` or `syndication` as the API for tweet extraction. Has no effect if logged in

#### stacommu, wrestleuniverse
* `device_id`: UUID value assigned by the website and used to enforce device limits for paid livestream content. Can be found in browser local storage

#### twitch
* `client_id`: Client ID value to be sent with GraphQL requests, e.g. `twitch:client_id=kimne78kx3ncx6brgo4mv6wki5h1ko`

#### nhkradirulive (NHK らじる★らじる LIVE)
* `area`: Which regional variation to extract. Valid areas are: `sapporo`, `sendai`, `tokyo`, `nagoya`, `osaka`, `hiroshima`, `matsuyama`, `fukuoka`. Defaults to `tokyo`

#### nflplusreplay
* `type`: Type(s) of game replays to extract. Valid types are: `full_game`, `full_game_spanish`, `condensed_game` and `all_22`. You can use `all` to extract all available replay types, which is the default

#### jiocinema
* `refresh_token`: The `refreshToken` UUID from browser local storage can be passed to extend the life of your login session when logging in with `token` as username and the `accessToken` from browser local storage as password

#### jiosaavn
* `bitrate`: Audio bitrates to request. One or more of `16`, `32`, `64`, `128`, `320`. Default is `128,320`

#### afreecatvlive
* `cdn`: One or more CDN IDs to use with the API call for stream URLs, e.g. `gcp_cdn`, `gs_cdn_pc_app`, `gs_cdn_mobile_web`, `gs_cdn_pc_web`

#### soundcloud
* `formats`: Formats to request from the API. Requested values should be in the format of `{protocol}_{codec}`, e.g. `hls_opus,http_aac`. The `*` character functions as a wildcard, e.g. `*_mp3`, and can be passed by itself to request all formats. Known protocols include `http`, `hls` and `hls-aes`; known codecs include `aac`, `opus` and `mp3`. Original `download` formats are always extracted. Default is `http_aac,hls_aac,http_opus,hls_opus,http_mp3,hls_mp3`

#### orfon (orf:on)
* `prefer_segments_playlist`: Prefer a playlist of program segments instead of a single complete video when available. If individual segments are desired, use `--concat-playlist never --extractor-args "orfon:prefer_segments_playlist"`

#### bilibili
* `prefer_multi_flv`: Prefer extracting flv formats over mp4 for older videos that still provide legacy formats

#### sonylivseries
* `sort_order`: Episode sort order for series extraction - one of `asc` (ascending, oldest first) or `desc` (descending, newest first). Default is `asc`

#### streaks
* `api_key`: API key for the `X-Streaks-Api-Key` header

#### tver
* `backend`: Backend API to use for extraction - one of `streaks` (default) or `brightcove` (deprecated)

#### vimeo
* `client`: Client to extract video data from. The currently available clients are `android` and `web`. Only one client can be used. The `web` client is used by default, and it only works with account cookies or login credentials. The `android` client only works with previously cached OAuth tokens
* `original_format_policy`: Policy for when to try extracting original formats. One of `always`, `never`, or `auto`. The default `auto` policy tries to avoid exceeding the web client's API rate-limit by only making an extra request when Vimeo publicizes the video's downloadability

#### adn
* `profile_id`: The numeric ID of the premium account profile that will be used to download videos (default: `1`)

#### zan
* `split_angles`: Split multi-angle streams into separate angle formats. Forces re-encoding of the video stream during download, and requires ffmpeg. Either `true` or `false` (default)

**Note**: These options may be changed/removed in the future without concern for backward compatibility

<!-- MANPAGE: MOVE "INSTALLATION" SECTION HERE -->


# PLUGINS

Note that **all** plugins are imported even if not invoked, and that **there are no checks** performed on plugin code. **Use plugins at your own risk and only if you trust the code!**

Plugins can be of `<type>`s `extractor` or `postprocessor`.
- Extractor plugins do not need to be enabled from the CLI and are automatically invoked when the input URL is suitable for it.
- Extractor plugins take priority over built-in extractors.
- Postprocessor plugins can be invoked using `--use-postprocessor NAME`.


Plugins are loaded from the namespace packages `yt_dlp_plugins.extractor` and `yt_dlp_plugins.postprocessor`.

In other words, the file structure on the disk looks something like:

        yt_dlp_plugins/
            extractor/
                myplugin.py
            postprocessor/
                myplugin.py

yt-ai looks for these `yt_dlp_plugins` namespace folders in many locations (see below) and loads in plugins from **all** of them.
Set the environment variable `YTDLP_NO_PLUGINS` to something nonempty to disable loading plugins entirely.

See the [wiki for some known plugins](https://github.com/yt-dlp/yt-dlp/wiki/Plugins)

## Installing Plugins

Plugins can be installed using various methods and locations.

1. **Configuration directories**:
   Plugin packages (containing a `yt_dlp_plugins` namespace folder) can be dropped into the following standard [configuration locations](#configuration):
    * **User Plugins**
      * `${XDG_CONFIG_HOME}/yt-ai/plugins/<package name>/yt_dlp_plugins/` (recommended on Linux/macOS)
      * `${XDG_CONFIG_HOME}/yt-ai-plugins/<package name>/yt_dlp_plugins/`
      * `${APPDATA}/yt-ai/plugins/<package name>/yt_dlp_plugins/` (recommended on Windows)
      * `${APPDATA}/yt-ai-plugins/<package name>/yt_dlp_plugins/`
      * `~/.yt-ai/plugins/<package name>/yt_dlp_plugins/`
      * `~/yt-ai-plugins/<package name>/yt_dlp_plugins/`
    * **System Plugins**
      * `/etc/yt-ai/plugins/<package name>/yt_dlp_plugins/`
      * `/etc/yt-ai-plugins/<package name>/yt_dlp_plugins/`
2. **Executable location**: Plugin packages can similarly be installed in a `yt-ai-plugins` directory under the executable location (recommended for portable installations):
    * Binary: where `<root-dir>/yt-ai.exe`, `<root-dir>/yt-ai-plugins/<package name>/yt_dlp_plugins/`
    * Source: where `<root-dir>/yt_dlp/__main__.py`, `<root-dir>/yt-ai-plugins/<package name>/yt_dlp_plugins/`

3. **pip and other locations in `PYTHONPATH`**
    * Plugin packages can be installed and managed using `pip`. See [yt-dlp-sample-plugins](https://github.com/yt-dlp/yt-dlp-sample-plugins) for an example.
      * Note: plugin files between plugin packages installed with pip must have unique filenames.
    * Any path in `PYTHONPATH` is searched in for the `yt_dlp_plugins` namespace folder.
      * Note: This does not apply for Pyinstaller builds.


`.zip`, `.egg` and `.whl` archives containing a `yt_dlp_plugins` namespace folder in their root are also supported as plugin packages.

* e.g. `${XDG_CONFIG_HOME}/yt-ai/plugins/mypluginpkg.zip` where `mypluginpkg.zip` contains `yt_dlp_plugins/<type>/myplugin.py`

Run yt-ai with `--verbose` to check if the plugin has been loaded.

## Developing Plugins

See the [yt-dlp-sample-plugins](https://github.com/yt-dlp/yt-dlp-sample-plugins) repo for a template plugin package and the [Plugin Development](https://github.com/yt-dlp/yt-dlp/wiki/Plugin-Development) section of the wiki for a plugin development guide.

All public classes with a name ending in `IE`/`PP` are imported from each file for extractors and postprocessors respectively. This respects underscore prefix (e.g. `_MyBasePluginIE` is private) and `__all__`. Modules can similarly be excluded by prefixing the module name with an underscore (e.g. `_myplugin.py`).

To replace an existing extractor with a subclass of one, set the `plugin_name` class keyword argument (e.g. `class MyPluginIE(ABuiltInIE, plugin_name='myplugin')` will replace `ABuiltInIE` with `MyPluginIE`). Since the extractor replaces the parent, you should exclude the subclass extractor from being imported separately by making it private using one of the methods described above.

If you are a plugin author, add [yt-dlp-plugins](https://github.com/topics/yt-dlp-plugins) as a topic to your repository for discoverability.

See the [Developer Instructions](https://github.com/CrimsonGlory/yt-ai/blob/master/CONTRIBUTING.md#developer-instructions) on how to write and test an extractor.

# EMBEDDING YT-AI

yt-ai makes the best effort to be a good command-line program, and thus should be callable from any programming language.

Your program should avoid parsing the normal stdout since they may change in future versions. Instead, they should use options such as `-J`, `--print`, `--progress-template`, `--exec` etc to create console output that you can reliably reproduce and parse.

From a Python program, you can embed yt-ai in a more powerful fashion, like this:

```python
from yt_dlp import YoutubeDL

URLS = ['https://www.youtube.com/watch?v=YE7VzlLtp-4']
with YoutubeDL() as ydl:
    ydl.download(URLS)
```

Most likely, you'll want to use various options. For a list of options available, have a look at [`yt_dlp/YoutubeDL.py`](yt_dlp/YoutubeDL.py#L183) or `help(yt_dlp.YoutubeDL)` in a Python shell. If you are already familiar with the CLI, you can use [`devscripts/cli_to_api.py`](https://github.com/CrimsonGlory/yt-ai/blob/master/devscripts/cli_to_api.py) to translate any CLI switches to `YoutubeDL` params.

**Tip**: If you are porting your code from youtube-dl to yt-ai, one important point to look out for is that we do not guarantee the return value of `YoutubeDL.extract_info` to be json serializable, or even be a dictionary. It will be dictionary-like, but if you want to ensure it is a serializable dictionary, pass it through `YoutubeDL.sanitize_info` as shown in the [example below](#extracting-information)

## Embedding examples

#### Extracting information

```python
import json
import yt_dlp

URL = 'https://www.youtube.com/watch?v=YE7VzlLtp-4'

# ℹ️ See help(yt_dlp.YoutubeDL) for a list of available options and public functions
ydl_opts = {}
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(URL, download=False)

    # ℹ️ ydl.sanitize_info makes the info json-serializable
    print(json.dumps(ydl.sanitize_info(info)))
```
#### Download using an info-json

```python
import yt_dlp

INFO_FILE = 'path/to/video.info.json'

with yt_dlp.YoutubeDL() as ydl:
    error_code = ydl.download_with_info_file(INFO_FILE)

print('Some videos failed to download' if error_code
      else 'All videos successfully downloaded')
```

#### Extract audio

```python
import yt_dlp

URLS = ['https://www.youtube.com/watch?v=YE7VzlLtp-4']

ydl_opts = {
    'format': 'm4a/bestaudio/best',
    # ℹ️ See help(yt_dlp.postprocessor) for a list of available Postprocessors and their arguments
    'postprocessors': [{  # Extract audio using ffmpeg
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'm4a',
    }]
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    error_code = ydl.download(URLS)
```

#### Filter videos

```python
import yt_dlp

URLS = ['https://www.youtube.com/watch?v=YE7VzlLtp-4']

def longer_than_a_minute(info, *, incomplete):
    """Download only videos longer than a minute (or with unknown duration)"""
    duration = info.get('duration')
    if duration and duration < 60:
        return 'The video is too short'

ydl_opts = {
    'match_filter': longer_than_a_minute,
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    error_code = ydl.download(URLS)
```

#### Adding logger and progress hook

```python
import yt_dlp

URLS = ['https://www.youtube.com/watch?v=YE7VzlLtp-4']

class MyLogger:
    def debug(self, msg):
        # For compatibility with youtube-dl, both debug and info are passed into debug
        # You can distinguish them by the prefix '[debug] '
        if msg.startswith('[debug] '):
            pass
        else:
            self.info(msg)

    def info(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)


# ℹ️ See "progress_hooks" in help(yt_dlp.YoutubeDL)
def my_hook(d):
    if d['status'] == 'finished':
        print('Done downloading, now post-processing ...')


ydl_opts = {
    'logger': MyLogger(),
    'progress_hooks': [my_hook],
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download(URLS)
```

#### Add a custom PostProcessor

```python
import yt_dlp

URLS = ['https://www.youtube.com/watch?v=YE7VzlLtp-4']

# ℹ️ See help(yt_dlp.postprocessor.PostProcessor)
class MyCustomPP(yt_dlp.postprocessor.PostProcessor):
    def run(self, info):
        self.to_screen('Doing stuff')
        return [], info


with yt_dlp.YoutubeDL() as ydl:
    # ℹ️ "when" can take any value in yt_dlp.utils.POSTPROCESS_WHEN
    ydl.add_post_processor(MyCustomPP(), when='pre_process')
    ydl.download(URLS)
```


#### Use a custom format selector

```python
import yt_dlp

URLS = ['https://www.youtube.com/watch?v=YE7VzlLtp-4']

def format_selector(ctx):
    """ Select the best video and the best audio that won't result in an mkv.
    NOTE: This is just an example and does not handle all cases """

    # formats are already sorted worst to best
    formats = ctx.get('formats')[::-1]

    # acodec='none' means there is no audio
    best_video = next(f for f in formats
                      if f['vcodec'] != 'none' and f['acodec'] == 'none')

    # find compatible audio extension
    audio_ext = {'mp4': 'm4a', 'webm': 'webm'}[best_video['ext']]
    # vcodec='none' means there is no video
    best_audio = next(f for f in formats if (
        f['acodec'] != 'none' and f['vcodec'] == 'none' and f['ext'] == audio_ext))

    # These are the minimum required fields for a merged format
    yield {
        'format_id': f'{best_video["format_id"]}+{best_audio["format_id"]}',
        'ext': best_video['ext'],
        'requested_formats': [best_video, best_audio],
        # Must be + separated list of protocols
        'protocol': f'{best_video["protocol"]}+{best_audio["protocol"]}'
    }


ydl_opts = {
    'format': format_selector,
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download(URLS)
```


# CHANGES FROM YT-DLP

yt-ai is a fork of [yt-dlp](https://github.com/yt-dlp/yt-dlp). Download defaults, format selection, and most options are the same. This section lists the changes made in this fork.

### New features

* Forked from [**yt-dlp**](https://github.com/yt-dlp/yt-dlp) and periodically merged with upstream (currently through [**yt-dlp@bbc809a11**](https://github.com/yt-dlp/yt-dlp/commit/bbc809a1161d3bfca51fa36f59dda35556ee85a0))

* **Independent branding**: Binaries, config, cache, and plugin paths use `yt-ai`, so yt-ai can be installed alongside yt-dlp. The Python import remains `yt_dlp`. See [CONFIGURATION](#configuration)

* **AI/LLM contributions required**: yt-dlp's NO AI / NO LLM contribution ban (`.NO_AI`, issue/PR checkboxes, and auto-close workflow) has been replaced with [`.NO_HUMAN`](.NO_HUMAN/README.md)

* **Restored extractors previously blocked as piracy**: The KnownPiracy refusal list is gone. Restored from git history (and youtube-dl for viewsb): DoodStream, viewsb (StreamSB), filemoon, HentaiStigma, ThisAV, XFileShare hosts, YourPorn (sxyprn), Jable, 91porn, Einthusan, YourUpload, Xanimu, Musicdex, duboku, and Gofile

* **Restored extractors previously marked currently broken**: Sites that still publish media were rewritten against current pages/APIs. Notable reworks include DW, Europa, TFO, TeleMB, PlutoTV, and GDCVault. Extractors whose old APIs died can fall back to HTML5 / JSON-LD / JWPlayer / HLS on the webpage (`_WEB_FALLBACK`)

* **New extractors**:
    * **3m** (`3m.com`): Product-page `__INITIAL_DATA` Brightcove gallery (`videoPlayerListId`) via the snaps2 player map. Request: [yt-dlp/yt-dlp#15705](https://github.com/yt-dlp/yt-dlp/issues/15705)
    * **Abyss** (`abyss.to`): Decrypt player `datas` (AES-CTR) and download `sssrr.org` sora MP4 fragments. Request: [yt-dlp/yt-dlp#16027](https://github.com/yt-dlp/yt-dlp/issues/16027)
    * **acmi** (`acmi.net.au`): Public XOS `/xos/works/{id}/` JSON and signed S3 `web_resource`/`resource` MP4s. Request: [yt-dlp/yt-dlp#5974](https://github.com/yt-dlp/yt-dlp/issues/5974)
    * **AdobeMax** (`adobe.com`): MAX `/sessions/` pages load `/www-fragments/max/{year}/marquees/{code}/ondemand.live.html` and delegate the `video.tv.adobe.com` iframe to **adobetv**. Request: [yt-dlp/yt-dlp#7992](https://github.com/yt-dlp/yt-dlp/issues/7992)
    * **AdultEmpire** (`adultempire.com`): Age-gate cookie, then `/gw/player` JSON-LD `contentUrl` trailer MP4. Request: [yt-dlp/yt-dlp#9583](https://github.com/yt-dlp/yt-dlp/issues/9583)
    * **afl** (`afl.com.au`): Brightcove `video-js` player IDs from public `/video/` pages. Request: [yt-dlp/yt-dlp#10909](https://github.com/yt-dlp/yt-dlp/issues/10909)
    * **AiryTV** (`live.airy.tv`): Public `api.airy.tv` `/content/{id}` JSON for unencrypted VOD HLS. Request: [yt-dlp/yt-dlp#14937](https://github.com/yt-dlp/yt-dlp/issues/14937)
    * **AllDaf** (`alldaf.org`): Nuxt `__NUXT_DATA__` post `s3Url`/HLS plus JWPlayer media JSON. Request: [yt-dlp/yt-dlp#15289](https://github.com/yt-dlp/yt-dlp/issues/15289)
    * **AlphaTV** (`alphatv.gr`): Kwik player `data-video-url` MP4/HLS with JSON-LD `embedUrl` fallback. Request: [yt-dlp/yt-dlp#14945](https://github.com/yt-dlp/yt-dlp/issues/14945)
    * **AnimationFilmArchives** (`animation.filmarchives.jp`): NII `h10.cs.nii.ac.jp` iframe DASH/HLS (`video_view.php`) from play and playen pages. Request: [yt-dlp/yt-dlp#8982](https://github.com/yt-dlp/yt-dlp/issues/8982)
    * [AnonMP4](https://github.com/CrimsonGlory/yt-ai/commit/7e1d8ceb53acea50102343d0cd3db56e1fc2dbc8) (`anonmp4.art` / `anonmp4.to`)
    * **Archivebate** (`archivebate.com`): Mixdrop iframe packed `MDCore.wurl` MP4, with native HLS embed fallback. Request: [yt-dlp/yt-dlp#8262](https://github.com/yt-dlp/yt-dlp/issues/8262)
    * **AsianGamesHub** (`asiangameshub.com`): Anonymous ViewLift identity token and entitlement HLS/MP4. Request: [yt-dlp/yt-dlp#12861](https://github.com/yt-dlp/yt-dlp/issues/12861)
    * **AsianPinay** (`asianpinay.cc`): XtremeStream player `xs1.php` HLS from the iframe embed, with Magixz CDN MP4 fallback. Request: [yt-dlp/yt-dlp#7132](https://github.com/yt-dlp/yt-dlp/issues/7132)
    * **AstalaVR** (`astalavr.com`): Impersonate Cloudflare and extract Delight VR (`dl8-video`) tokened MP4 sources. Request: [yt-dlp/yt-dlp#13332](https://github.com/yt-dlp/yt-dlp/issues/13332)
    * **ATPTour** (`atptour.com`): Impersonate Cloudflare, then Brightcove IDs from `/videos/getcurrentrelatedvideos` and news-page `video-js`/iframe embeds. Request: [yt-dlp/yt-dlp#10816](https://github.com/yt-dlp/yt-dlp/issues/10816)
    * **Avjb** (`avjb.com`): Player CSRF `/player/spped.php` HLS lines, with Playerjs preview MP4 fallback. Request: [yt-dlp/yt-dlp#14653](https://github.com/yt-dlp/yt-dlp/issues/14653)
    * **AzNude** (`aznude.com`): JWPlayer `playerInstance.setup` HLS/MP4 from `/azncdn/` and `/embed/` pages; celeb/movie listings as playlists. Request: [yt-dlp/yt-dlp#12060](https://github.com/yt-dlp/yt-dlp/issues/12060)
    * **B9Good** (`b9good.org`): korxime.guru JWPlayer embed; signed `/ajax/getSources` AES-GCM HLS. Request: [yt-dlp/yt-dlp#9245](https://github.com/yt-dlp/yt-dlp/issues/9245)
    * **BaiduBaike** (`baike.baidu.com`): Impersonate Baidu WAF, then 秒懂 `/api/wikisecond/lemmasecond` and `/api/second/video` MP4/HLS. Request: [yt-dlp/yt-dlp#7467](https://github.com/yt-dlp/yt-dlp/issues/7467)
    * **Balapan** (`balapan.tv`): Clappr HLS from the `player.rtrk.kz` live iframe. Request: [yt-dlp/yt-dlp#17241](https://github.com/yt-dlp/yt-dlp/issues/17241)
    * **BaoMoi** (`baomoi.com`): Public `w-api.baomoi.com` `/page/get/content-detail` JSON and signed `bmcdn.me` MP4, with `__NEXT_DATA__` fallback. Request: [yt-dlp/yt-dlp#7506](https://github.com/yt-dlp/yt-dlp/issues/7506)
    * **BeatStars** (`beatstars.com`): Public `main.v2.beatstars.com/track` JSON and tagged stream MP3. Request: [yt-dlp/yt-dlp#14675](https://github.com/yt-dlp/yt-dlp/issues/14675)
    * **BigMarker** (`bigmarker.com`): Conference-page `bmVideoPlayer.loadVideo` progressive MP4, plus HLS/DASH when unencrypted. Request: [yt-dlp/yt-dlp#13694](https://github.com/yt-dlp/yt-dlp/issues/13694)
    * **Blacksky** (`blacksky.community`): AT Protocol `getPostThread` via `api.blacksky.community` (HLS on `video.blacksky.community`, blob fallback from the author's PDS). Request: [yt-dlp/yt-dlp#16161](https://github.com/yt-dlp/yt-dlp/issues/16161)
    * **Blod** (`blod.gr`): Impersonate Cloudflare, then `data-vimeo-id` player embed with JSON-LD lecture metadata. Request: [yt-dlp/yt-dlp#8471](https://github.com/yt-dlp/yt-dlp/issues/8471)
    * **BNRNews** (`bnrnews.bg`): Public `/api/materials/{program}/{id}` JSON and `/api/media/{uuid}` MP3/MP4. Request: [yt-dlp/yt-dlp#15248](https://github.com/yt-dlp/yt-dlp/issues/15248)
    * **Boomplay** (`boomplay.com`): Public `/share/getEventData` JSON and `source.boomplaymusic.com` MP3. Request: [yt-dlp/yt-dlp#11220](https://github.com/yt-dlp/yt-dlp/issues/11220)
    * **Boomstream** (`play.boomstream.com`): Player `window.boomstreamConfig` HLS; derive AES-128 key/IV from `#EXT-X-MEDIA-READY`. Request: [yt-dlp/yt-dlp#15376](https://github.com/yt-dlp/yt-dlp/issues/15376)
    * **BoyfriendTV** (`boyfriendtv.com`): Player `sources.hlsAuto` HLS from video pages. Request: [yt-dlp/yt-dlp#15509](https://github.com/yt-dlp/yt-dlp/issues/15509)
    * **Bouke** (`bouke.media`): Drupal Freecaster `data-video-id` / `live_token` embed JSON (MP4, HLS, DASH). Request: [yt-dlp/yt-dlp#15403](https://github.com/yt-dlp/yt-dlp/issues/15403)
    * **Brighteon** (`brighteon.com`): Next.js `__NEXT_DATA__` HLS/DASH and `/api-v3/channels` listings. Request: [yt-dlp/yt-dlp#8214](https://github.com/yt-dlp/yt-dlp/issues/8214)
    * **Brollie** (`brollie.com.au`): MAZ catalog `item_feeds` plus anonymous Zype HLS from `api.maz.tv`. Request: [yt-dlp/yt-dlp#15164](https://github.com/yt-dlp/yt-dlp/issues/15164)
    * **Bunkr** (`bunkr.cr`): File-page `data-file-id` via `dl.bunkr.cr/api/_001_v2` and signed CDN URL from `glb-apisign.cdn.cr`. Request: [yt-dlp/yt-dlp#12536](https://github.com/yt-dlp/yt-dlp/issues/12536)
    * **cablecast** (`cablecast.tv`): Public `/cablecastapi/v1` show/VOD JSON and HLS/MP4. Request: [yt-dlp/yt-dlp#9785](https://github.com/yt-dlp/yt-dlp/issues/9785)
    * **Camwhoresbay** (`camwhoresbay.com`): KVS `kt_player` `flashvars` and license-decoded `get_file` MP4s. Request: [yt-dlp/yt-dlp#11625](https://github.com/yt-dlp/yt-dlp/issues/11625)
    * **CaracolRadio** (`caracol.com.co`): Fusion `mediateca-info` JSON for public `/audio/` podcast and radio MP3s. Request: [yt-dlp/yt-dlp#6000](https://github.com/yt-dlp/yt-dlp/issues/6000)
    * **Castbox** (`castbox.fm`): Public `everest.castbox.fm` episode v4 JSON (direct MP3/media URL). Request: [yt-dlp/yt-dlp#16910](https://github.com/yt-dlp/yt-dlp/issues/16910)
    * **CBN** (`cbn.com`): Drupal `_format=json` Brightcove IDs with `video-js` / html5player fallback. Request: [yt-dlp/yt-dlp#15622](https://github.com/yt-dlp/yt-dlp/issues/15622)
    * **chaos.social** (`chaos.social`): Public Mastodon `/api/v1/statuses/{id}` JSON for toot video/audio attachments and account metadata. Request: [yt-dlp/yt-dlp#5589](https://github.com/yt-dlp/yt-dlp/issues/5589)
    * **Chapman** (`blogs.chapman.edu`): Impersonate Cloudflare on archive posts, then YuJa `/P/Data/VideoJSON` and `/P/Data/VideoSource` HLS. Request: [yt-dlp/yt-dlp#11127](https://github.com/yt-dlp/yt-dlp/issues/11127)
    * **Cime** (`ci.me`): Public `/api/app` JSON for VOD HLS, clip MP4, and Amazon IVS live. Request: [yt-dlp/yt-dlp#16247](https://github.com/yt-dlp/yt-dlp/issues/16247)
    * **CinemathequeBretagne** (`cinematheque-bretagne.bzh`): Diaz oEmbed iframe HTML5 MP4. Request: [yt-dlp/yt-dlp#15616](https://github.com/yt-dlp/yt-dlp/issues/15616)
    * **Cinetimes** (`cinetimes.org`): Title-page Plyr iframe (YouTube, archive.org, Vimeo) and Wikimedia Commons HTML5. Request: [yt-dlp/yt-dlp#7317](https://github.com/yt-dlp/yt-dlp/issues/7317)
    * **CollabInc** (`collab.inc`): Public `dashboard.collab.inc/api/public_video_library/{id}` JSON and S3 HLS, preferring unwatermarked `/hls/`. Request: [yt-dlp/yt-dlp#10080](https://github.com/yt-dlp/yt-dlp/issues/10080)
    * **college-de-france** (`college-de-france.fr`): JSON-LD `VideoObject` YouTube `embedUrl` with `podcastfichiers` m4a fallback. Request: [yt-dlp/yt-dlp#5991](https://github.com/yt-dlp/yt-dlp/issues/5991)
    * **CommercialRadio** (`881903.com`): Public `/api/live/src` playlist.js and CloudFront-cookie HLS (`edge-aac`/`edge-ts`). Request: [yt-dlp/yt-dlp#12241](https://github.com/yt-dlp/yt-dlp/issues/12241)
    * **ctc** (`ctc.ru`): Impersonate WAF for `/api/page/v1` JSON, then Odysseus playlist HLS/DASH via `X-Referer`. Request: [yt-dlp/yt-dlp#11162](https://github.com/yt-dlp/yt-dlp/issues/11162)
    * **CuriosityU** (`curiosityu.com`): Bitmovin DASH (`cdn-s3-cf.curiositystream.com`) from lecture-page `sourceConfig`. Request: [yt-dlp/yt-dlp#16564](https://github.com/yt-dlp/yt-dlp/issues/16564)
    * **Cyberfile** (`cyberfile.me`): YetiShare `account/ajax/file_details` download_token MP4s and folder listings. Request: [yt-dlp/yt-dlp#8932](https://github.com/yt-dlp/yt-dlp/issues/8932)
    * **DanmarkPaaFilm** (`danmarkpaafilm.dk`): Impersonate, then Drupal `/player-playback-url` DBC AMS iframe and AES-128 HLS. Request: [yt-dlp/yt-dlp#8316](https://github.com/yt-dlp/yt-dlp/issues/8316)
    * **DeviantArt** (`deviantart.com`): Eclipse `__INITIAL_STATE__` transcoded MP4s with JSON-LD `contentUrl` fallback. Request: [yt-dlp/yt-dlp#17234](https://github.com/yt-dlp/yt-dlp/issues/17234)
    * **DI.FM** (`di.fm`): Impersonate Cloudflare, then AudioAddict episode JSON and signed `content.audioaddict.com` AAC. Request: [yt-dlp/yt-dlp#12520](https://github.com/yt-dlp/yt-dlp/issues/12520)
    * **DigitalerLesesaal** (`digitaler-lesesaal.bundesarchiv.de`): Public archive video/copies JSON and liXe player HLS. Request: [yt-dlp/yt-dlp#10451](https://github.com/yt-dlp/yt-dlp/issues/10451)
    * **DoramasPrincess** (`doramasprincess.com`): POST `/ajax/embed` for HTML5 sources and packed JWPlayer HLS from host iframes. Request: [yt-dlp/yt-dlp#16369](https://github.com/yt-dlp/yt-dlp/issues/16369)
    * **Emturbovid** (`emturbovid.com`): JWPlayer `urlPlay` HLS; skip PNG-wrapped Google Drive segments with `EXT-X-BYTERANGE`. Request: [yt-dlp/yt-dlp#6869](https://github.com/yt-dlp/yt-dlp/issues/6869)
    * **EpicDeveloperCommunity** (`dev.epicgames.com`): Impersonate Cloudflare, then learning `post.json` plus Electra/qstv DASH. Request: [yt-dlp/yt-dlp#9783](https://github.com/yt-dlp/yt-dlp/issues/9783)
    * **eplay** (`eplay.com`): Public `search-cf.eplay.com` post JSON (tokenized MP4/HLS) with Next.js fallback. Request: [yt-dlp/yt-dlp#16853](https://github.com/yt-dlp/yt-dlp/issues/16853)
    * **Erothots** (`erothots.co`): JSON-LD metadata and Plyr/Video.js HTML5 MP4 from `cdn.erocdn.co`. Request: [yt-dlp/yt-dlp#13021](https://github.com/yt-dlp/yt-dlp/issues/13021)
    * **EsupPod** (`pod.univ-lille.fr`): Video.js `mp4_sources` progressive MP4, with `srcOptions` HLS fallback. Request: [yt-dlp/yt-dlp#13738](https://github.com/yt-dlp/yt-dlp/issues/13738)
    * **ExtremeMusic** (`extrememusic.com`): Public `snapi.extrememusic.com` track/album/playlist JSON and CloudFront audition MP3s. Request: [yt-dlp/yt-dlp#10997](https://github.com/yt-dlp/yt-dlp/issues/10997)
    * **Fawesome** (`fawesome.tv`): Security-token `recipes.php` API for HLS and progressive MP4. Request: [yt-dlp/yt-dlp#15706](https://github.com/yt-dlp/yt-dlp/issues/15706)
    * **FikFap** (`fikfap.com`): Public `api.fikfap.com` post JSON (anonymous UUID) and tokenized Bunny HLS. Request: [yt-dlp/yt-dlp#14980](https://github.com/yt-dlp/yt-dlp/issues/14980)
    * **Filmzie** (`filmzie.com`): Public `/api/v1/content` metadata and `/api/v1/video/stream` HLS. Request: [yt-dlp/yt-dlp#14535](https://github.com/yt-dlp/yt-dlp/issues/14535)
    * **Forendors** (`forendors.cz`): Public `api.forendors.cz` post JSON and signed `assets.forendors.cz` HLS. Request: [yt-dlp/yt-dlp#15173](https://github.com/yt-dlp/yt-dlp/issues/15173)
    * **FOX4KC** (`fox4kc.com`): Anvato/Lura HLS from `/video/{slug}/{id}/` URLs and WordPress `lead_media` on article pages. Request: [yt-dlp/yt-dlp#16582](https://github.com/yt-dlp/yt-dlp/issues/16582)
    * **FreeSex** (`freesex.cz`): POST the 18+ terms form and extract the Video.js HTML5 MP4. Request: [yt-dlp/yt-dlp#15930](https://github.com/yt-dlp/yt-dlp/issues/15930)
    * **Funkwhale** (`funk.firobe.fr`): Public `/api/v1` track, playlist, album, and channel JSON plus `/api/v1/listen` audio. Request: [yt-dlp/yt-dlp#7627](https://github.com/yt-dlp/yt-dlp/issues/7627)
    * **Fyptt** (`fyptt.to`): ARVE iframe to Video.js `fypttstr.php` / JWPlayer `fypttjwstr.php` and tokenized `stream.fyptt.to` MP4. Request: [yt-dlp/yt-dlp#7998](https://github.com/yt-dlp/yt-dlp/issues/7998)
    * **Gayhaus** (`gayhaus.com`): KVS `kt_player` config (randomized JS object) and license-decoded `get_file` MP4s. Request: [yt-dlp/yt-dlp#12384](https://github.com/yt-dlp/yt-dlp/issues/12384)
    * **ge.movie** (`ge.movie`): Impersonate Cloudflare, then Playerjs playlists from the `em.filmix.stream` / `em.kinoflix.tv` iframe. Request: [yt-dlp/yt-dlp#13390](https://github.com/yt-dlp/yt-dlp/issues/13390)
    * **Giphy** (`giphy.com`): Next.js gif JSON with unsigned `media.giphy.com` MP4/GIF/WebP (signed OG/v1 URLs return HTML). Request: [yt-dlp/yt-dlp#16970](https://github.com/yt-dlp/yt-dlp/issues/16970)
    * **GlobalNews** (`globalnews.ca`): JSON-LD `contentUrl` MP4 for `/video/` clips and JW `video-entry` HLS for `/live/` streams. Request: [yt-dlp/yt-dlp#9266](https://github.com/yt-dlp/yt-dlp/issues/9266)
    * **GoogleMaps** (`maps.app.goo.gl`): Follow share/place URLs to `lh3.googleusercontent.com` progressive MP4s (`=m18`/`=m22`/`=m37`/`=dv`). Request: [yt-dlp/yt-dlp#12246](https://github.com/yt-dlp/yt-dlp/issues/12246)
    * **Granicus** (`harrisonburg-va.granicus.com`): Flowplayer `video_url` HLS from clip player pages. Request: [yt-dlp/yt-dlp#15344](https://github.com/yt-dlp/yt-dlp/issues/15344)
    * **Haokan** (`haokan.baidu.com`): Public `mbd.baidu.com` videolanding `window.jsonData` `clarityUrl`/`playurl` MP4. Request: [yt-dlp/yt-dlp#7069](https://github.com/yt-dlp/yt-dlp/issues/7069)
    * **Hobune** (`hobune.stream`): HTML5 video pages and static channel listings. Request: [yt-dlp/yt-dlp#17541](https://github.com/yt-dlp/yt-dlp/issues/17541)
    * **Hotmart** (`player.hotmart.com`): Next.js `__NEXT_DATA__` `applicationData` HLS (`vod-akm.play.hotmart.com`) with player Referer. Request: [yt-dlp/yt-dlp#8397](https://github.com/yt-dlp/yt-dlp/issues/8397)
    * **HQPorner** (`hqporner.com`): Player iframe (mydaddy.cc) HTML5 MP4 sources. Request: [yt-dlp/yt-dlp#7116](https://github.com/yt-dlp/yt-dlp/issues/7116)
    * **hstream** (`hstream.moe`): Laravel `/player/api` JSON for progressive 720p MP4 and DASH (including 48fps). Request: [yt-dlp/yt-dlp#9791](https://github.com/yt-dlp/yt-dlp/issues/9791)
    * **Hudl** (`hudl.com`): Public fan GraphQL broadcast JSON and vcloud HLS. Request: [yt-dlp/yt-dlp#9022](https://github.com/yt-dlp/yt-dlp/issues/9022)
    * **Hypeddit** (`hypeddit.com`): Public `hypeddit-gates-prod` S3 preview MP3 from gate pages. Request: [yt-dlp/yt-dlp#7948](https://github.com/yt-dlp/yt-dlp/issues/7948)
    * **IcePorn** (`iceporn.com`): Public `/player_config_json/` MP4 files (DrTuber-style API). Request: [yt-dlp/yt-dlp#12478](https://github.com/yt-dlp/yt-dlp/issues/12478)
    * **IFunny** (`ifunny.co` / `img.ifunny.co`): Video-page Open Graph/HTML5 MP4 (`img.getfn.io` / `img.ifunny.co`) and CSRF `/api/v1/user/{nick}/timeline` playlists. Request: [yt-dlp/yt-dlp#8006](https://github.com/yt-dlp/yt-dlp/issues/8006)
    * **ImagenTV** (`imagentv.com`): Dailymotion (and YouTube) IDs from Drupal `itv_content_result` and the public livestreaming API. Request: [yt-dlp/yt-dlp#16391](https://github.com/yt-dlp/yt-dlp/issues/16391)
    * **InfosecExchange** (`video.infosec.exchange`): PeerTube `/api/v1/videos` JSON for HLS and fragmented MP4. Request: [yt-dlp/yt-dlp#11857](https://github.com/yt-dlp/yt-dlp/issues/11857)
    * **ipfs** (`ipfs://`): Rewrite `ipfs://`/`ipns://` CIDs to an HTTP gateway (`--extractor-args ipfs:gateway=URL`, `IPFS_GATEWAY`, or Pinata). Request: [yt-dlp/yt-dlp#6860](https://github.com/yt-dlp/yt-dlp/issues/6860)
    * **JavGuru** (`jav.guru`): Impersonate Cloudflare, decode `wp-btn-iframe` searcho tokens, then DoodStream/packed HLS host embeds. Request: [yt-dlp/yt-dlp#6393](https://github.com/yt-dlp/yt-dlp/issues/6393)
    * **Javtiful** (`javtiful.com`): Plyr `playerSources` HTML5 MP4 with JSON-LD metadata. Request: [yt-dlp/yt-dlp#12280](https://github.com/yt-dlp/yt-dlp/issues/12280)
    * **JCBASimul** (`jcbasimul.com`): Radimo `select_stream` JWT plus Ogg Opus over WebSocket (`listener.fmplapla.com`). Request: [yt-dlp/yt-dlp#14092](https://github.com/yt-dlp/yt-dlp/issues/14092)
    * **KamTape** (`kamtape.com`): VLPlayer `get_video` (HTML5 MP4) from watch pages. Request: [yt-dlp/yt-dlp#17508](https://github.com/yt-dlp/yt-dlp/issues/17508)
    * **Kan** (`kan.org.il`): Impersonate Cloudflare, then RedGalaxy `data-redge-config` HLS for VOD/live and `audioPlayerPlaylist` Omny MP3 for podcasts. Request: [yt-dlp/yt-dlp#13092](https://github.com/yt-dlp/yt-dlp/issues/13092)
    * **Karafun** (`karafun.com`): Signed web-session `/api` plus `.kit` container Ogg-track extraction. Request: [yt-dlp/yt-dlp#15470](https://github.com/yt-dlp/yt-dlp/issues/15470)
    * **KaruselTV** (`karusel-tv.ru`): Public `video/api/get/{id}` MP4 sources from video and announce pages. Request: [yt-dlp/yt-dlp#17236](https://github.com/yt-dlp/yt-dlp/issues/17236)
    * **Keporn** (`f1.keporn.vip`): Public `/api/json/video` metadata and `/api/videofile.php` Cyrillic-base64 `get_file` MP4s. Request: [yt-dlp/yt-dlp#14612](https://github.com/yt-dlp/yt-dlp/issues/14612)
    * **KHInsider** (`downloads.khinsider.com`): Public MP3/FLAC CDN links from track pages; albums as track playlists. Request: [yt-dlp/yt-dlp#16713](https://github.com/yt-dlp/yt-dlp/issues/16713)
    * **KickBot** (`kickbot.app`): SvelteKit `__data.json` clip metadata and `clips.kickbotcdn.com` HLS/MP4. Request: [yt-dlp/yt-dlp#8861](https://github.com/yt-dlp/yt-dlp/issues/8861)
    * **Kidoodle** (`kidoodle.tv`): Folks guest token plus Albedo `content/episodes` AVOD HLS. Request: [yt-dlp/yt-dlp#6209](https://github.com/yt-dlp/yt-dlp/issues/6209)
    * **Kissasian** (`kissasian.video`): Follow `hndrama.cc` embed servers and packed JWPlayer HLS (VidHide). Request: [yt-dlp/yt-dlp#7801](https://github.com/yt-dlp/yt-dlp/issues/7801)
    * **Kuaishou** (`kuaishou.com`): Mobile H5 `window.INIT_STATE` progressive MP4/HLS from share and short-video pages. Request: [yt-dlp/yt-dlp#14010](https://github.com/yt-dlp/yt-dlp/issues/14010)
    * **KVF** (`kvf.fo`): JWPlayer `media`/`mode` vars and `vod.kringvarp.fo` SMIL HLS. Request: [yt-dlp/yt-dlp#9620](https://github.com/yt-dlp/yt-dlp/issues/9620)
    * **LearnEnglishKids** (`learnenglishkids.britishcouncil.org`): Drupal `akamai-custom-embed` Plyr HLS from `data-video`, with YouTube iframe fallback. Request: [yt-dlp/yt-dlp#10146](https://github.com/yt-dlp/yt-dlp/issues/10146)
    * **LookMovie2** (`lookmovie2.to`): Play-page `movie_storage`/`show_storage` hash plus `/api/v1/security/{movie,episode}-access` HLS. Request: [yt-dlp/yt-dlp#8951](https://github.com/yt-dlp/yt-dlp/issues/8951)
    * **LuluStream** (`luluvid.com`): Packed JWPlayer HLS from embed pages (CDN token is bound to User-Agent and Accept-Language). Request: [yt-dlp/yt-dlp#16656](https://github.com/yt-dlp/yt-dlp/issues/16656)
    * **Luticlip** (`luticlip.com`): HTML5 Video.js MP4 from RetroTube pages with Range-chunked takcdn downloads. Request: [yt-dlp/yt-dlp#16465](https://github.com/yt-dlp/yt-dlp/issues/16465)
    * **MacaulayLibrary** (`macaulaylibrary.org`): Solve Anubis PoW, then download Cornell CDN video/audio from asset pages. Request: [yt-dlp/yt-dlp#9292](https://github.com/yt-dlp/yt-dlp/issues/9292)
    * **Mat6Tube** (`mat6tube.com`): JWPlayer `window.playlist` progressive MP4s from watch pages. Request: [yt-dlp/yt-dlp#14613](https://github.com/yt-dlp/yt-dlp/issues/14613)
    * **MatreshkaTV** (`matreshka.tv`): Public `/api/video-service/v1/video/{id}` JSON for signed HLS on `c4-video.cmtv.ru`. Request: [yt-dlp/yt-dlp#15380](https://github.com/yt-dlp/yt-dlp/issues/15380)
    * **MeansTV** (`means.tv`): Uscreen `/program_content` Mux HLS; collections via `/collection_homepage`. Request: [yt-dlp/yt-dlp#12026](https://github.com/yt-dlp/yt-dlp/issues/12026)
    * **MeijiFilmArchives** (`meiji.filmarchives.jp`): NII `h10.cs.nii.ac.jp` iframe DASH/HLS (`video_view.php`) from work and Lumière pages. Request: [yt-dlp/yt-dlp#13035](https://github.com/yt-dlp/yt-dlp/issues/13035)
    * **Memobase** (`memobase.ch`): Non-Mozilla UA past Anubis, then Plyr `media.memobase.ch` `/master` MP4/M4V; SRG Play embeds delegated to **srgssr**. Request: [yt-dlp/yt-dlp#6820](https://github.com/yt-dlp/yt-dlp/issues/6820)
    * **Meridix** (`meridix.com`): Qwilt VOD HLS (`smil:http_ondemand/{id}.smil`, audio `mp4:http_ondemand/{id}.mp4`) with a site Referer. Request: [yt-dlp/yt-dlp#9230](https://github.com/yt-dlp/yt-dlp/issues/9230)
    * **Mfcamhub** (`mfcamhub.com`): KVS `kt_player` hashed flashvars and license-decoded `get_file` MP4s. Request: [yt-dlp/yt-dlp#10449](https://github.com/yt-dlp/yt-dlp/issues/10449)
    * **MGTOWTV** (`mgtow.tv`): PlayTube HTML5 `<source>` MP4s from watch and embed pages. Request: [yt-dlp/yt-dlp#7755](https://github.com/yt-dlp/yt-dlp/issues/7755)
    * **milb** (`milb.com`): `window.INIT_DATA` clip playbacks (MP4/HLS) from `/video/` highlight pages. Request: [yt-dlp/yt-dlp#7694](https://github.com/yt-dlp/yt-dlp/issues/7694)
    * **MissAV** (`missav`): Impersonate Cloudflare, unpack packed player JS, and download `surrit.com` HLS. Request: [yt-dlp/yt-dlp#11458](https://github.com/yt-dlp/yt-dlp/issues/11458)
    * **MissEvan** (`missevan.com`): Public `/sound/getsound` JSON for progressive M4A; SAMPLE-AES HLS is DRM. Request: [yt-dlp/yt-dlp#15517](https://github.com/yt-dlp/yt-dlp/issues/15517)
    * **MisterRogers** (`misterrogers.org`): Brightcove `video-js` player IDs from public `/videos/` clips and `/video-playlist/` pages. Request: [yt-dlp/yt-dlp#8263](https://github.com/yt-dlp/yt-dlp/issues/8263)
    * **MoverUz** (`mover.uz`): Decode obfuscated Playerjs `#2` config for labeled `v.mover.uz` MP4s. Request: [yt-dlp/yt-dlp#9579](https://github.com/yt-dlp/yt-dlp/issues/9579)
    * **Mp4Porn** (`mp4porn.space`): Player `url_v` `/play` MP4 and `/play_hls` HLS with a site Referer. Request: [yt-dlp/yt-dlp#15302](https://github.com/yt-dlp/yt-dlp/issues/15302)
    * **Mp4Upload** (`mp4upload.com`): Video.js `player.src` MP4 from embed pages with a site Referer. Request: [yt-dlp/yt-dlp#14075](https://github.com/yt-dlp/yt-dlp/issues/14075)
    * **Musi** (`feelthemusi.com`): Public `/api/v4/playlists/fetch` JSON and YouTube video IDs. Request: [yt-dlp/yt-dlp#12931](https://github.com/yt-dlp/yt-dlp/issues/12931)
    * **MusicBrainz** (`musicbrainz.org`): MusicBrainz WS/2 URL relationships, preferring YouTube/SoundCloud/Audius/Audiomack/Bandcamp. Request: [yt-dlp/yt-dlp#13673](https://github.com/yt-dlp/yt-dlp/issues/13673)
    * **MyNet** (`mynet.com`): Player `videoInfo` progressive MP4 and HLS from `/tv/embed/{id}`. Request: [yt-dlp/yt-dlp#7714](https://github.com/yt-dlp/yt-dlp/issues/7714)
    * **Naver:blog** (`blog.naver.com`): PostView `vid`/`inkey` (SE3 and Prism player) via the rmcnmv VOD play API. Request: [yt-dlp/yt-dlp#16816](https://github.com/yt-dlp/yt-dlp/issues/16816)
    * **NewsdayTV** (`newsday.tv`): Next.js `__NEXT_DATA__` Brightcove IDs from `/watch/` pages. Request: [yt-dlp/yt-dlp#7418](https://github.com/yt-dlp/yt-dlp/issues/7418)
    * **NewsNation** (`newsnationnow.com`): Anvato/Lura HLS from `/video/{slug}/{id}/` URLs and WordPress `lead_media` on article pages. Request: [yt-dlp/yt-dlp#7285](https://github.com/yt-dlp/yt-dlp/issues/7285)
    * **NFSA** (`nfsa.gov.au`): Public Sanity GROQ for collection items, then Vimeo player URLs (site referer) or Sanity CDN files. Request: [yt-dlp/yt-dlp#9593](https://github.com/yt-dlp/yt-dlp/issues/9593)
    * **NhacCuaTui** (`nhaccuatui.com`): Nuxt `__NUXT_DATA__` song/video `streamURL` MP3/MP4 (and FLAC when present). Request: [yt-dlp/yt-dlp#12329](https://github.com/yt-dlp/yt-dlp/issues/12329)
    * **nobody.live** (`nobody.live`): Public `/stream` JSON for a random zero-viewer Twitch channel, then Twitch HLS. Request: [yt-dlp/yt-dlp#13696](https://github.com/yt-dlp/yt-dlp/issues/13696)
    * **Nutson** (`nutson.us`): Guest `api.nutson.us` v3 session, then v2 `media/{id}` MP4s (`media_urls`). Request: [yt-dlp/yt-dlp#6947](https://github.com/yt-dlp/yt-dlp/issues/6947)
    * **NZRPlus** (`nzrplus.com`): Guest DCE/ImgGaming `v1/init` token, then VOD/live HLS/DASH. Request: [yt-dlp/yt-dlp#7875](https://github.com/yt-dlp/yt-dlp/issues/7875)
    * **Olevod** (`olevod.com`): Signed `api.olelive.com` `/v1/pub/vod/detail` HLS. Request: [yt-dlp/yt-dlp#9379](https://github.com/yt-dlp/yt-dlp/issues/9379)
    * **OnePodcast** (`onepodcast.it`): GEDI media-hub `audioSource` MP3 and Brightcove `videoSrc` MP4 from episode pages. Request: [yt-dlp/yt-dlp#16798](https://github.com/yt-dlp/yt-dlp/issues/16798)
    * **Owncast** (`live.retrostrange.com`): Public `/api/status` and `/api/config` JSON plus `/hls/stream.m3u8`. Request: [yt-dlp/yt-dlp#7111](https://github.com/yt-dlp/yt-dlp/issues/7111)
    * **Oyez** (`oyez.org`): Public `api.oyez.org` case JSON and `case_media` MP3 oral arguments/opinion announcements. Request: [yt-dlp/yt-dlp#7829](https://github.com/yt-dlp/yt-dlp/issues/7829)
    * **PaceGallery** (`pacegallery.com`): Lazy-loaded YouTube `data-id` embeds on exhibition and journal pages. Request: [yt-dlp/yt-dlp#8327](https://github.com/yt-dlp/yt-dlp/issues/8327)
    * **PandaVideo** (`pandavideo.com`): Player-embed HLS from `b-{library}.tv.pandavideo.com.br/{id}/playlist.m3u8`. Request: [yt-dlp/yt-dlp#13109](https://github.com/yt-dlp/yt-dlp/issues/13109)
    * **PalestineFilmInstitute** (`palestinefilminstitute.org`): Tokened CDN `watch/{id}` HLS (`share/hls.m3u8`) plus `meta.json` poster/subs; Squarespace pages that iframe the player. Request: [yt-dlp/yt-dlp#11282](https://github.com/yt-dlp/yt-dlp/issues/11282)
    * **Piczel** (`piczel.tv`): Public `/api/streams/{slug}` JSON for LL-HLS live (`playback.piczel.tv`) and recording MP4s. Request: [yt-dlp/yt-dlp#16032](https://github.com/yt-dlp/yt-dlp/issues/16032)
    * **Pillows** (`pillows.su`): SvelteKit `__data.json` (devalue) metadata and `api.pillows.su` original-file downloads. Request: [yt-dlp/yt-dlp#17426](https://github.com/yt-dlp/yt-dlp/issues/17426)
    * **PimpBunny** (`pimpbunny.com`): KVS `kt_player` config (randomized JS object) and license-decoded `get_file` MP4s. Request: [yt-dlp/yt-dlp#15333](https://github.com/yt-dlp/yt-dlp/issues/15333)
    * **PlanetWissen** (`planet-wissen.de`): Parse inline WDR `gseaInlineMediaData` HLS/MP4 (mdb and sophora players). Request: [yt-dlp/yt-dlp#7239](https://github.com/yt-dlp/yt-dlp/issues/7239)
    * **PMVHaven** (`pmvhaven.com`): Public `/api/videos/{id}` JSON for source MP4 and HLS. Request: [yt-dlp/yt-dlp#9831](https://github.com/yt-dlp/yt-dlp/issues/9831)
    * **Pops** (`pops.vn`): Next.js `__NEXT_DATA__` `videoDetail` YouTube IDs and native HLS `sourceLink`. Request: [yt-dlp/yt-dlp#6955](https://github.com/yt-dlp/yt-dlp/issues/6955)
    * **PornHat** (`pornhat.com`): FluidPlayer HTML5 `/get_file/` sources as HLS masters on `cdn.privatehost.com`. Request: [yt-dlp/yt-dlp#11852](https://github.com/yt-dlp/yt-dlp/issues/11852)
    * **PornLib** (`pornlib.com`): Public `/player_config_json/` MP4 files (lq/hq/4k). Request: [yt-dlp/yt-dlp#14614](https://github.com/yt-dlp/yt-dlp/issues/14614)
    * **PornSlash** (`pornslash.com`): HLS.js `loadSource` master playlist with `/media/report` host fallback. Request: [yt-dlp/yt-dlp#14768](https://github.com/yt-dlp/yt-dlp/issues/14768)
    * **PragmaticWorksTraining** (`learning.pragmaticworkstraining.com`): Public LMS `GetVideoPreview` / `GetCoursePublic*` JSON and Mux HLS. Request: [yt-dlp/yt-dlp#10188](https://github.com/yt-dlp/yt-dlp/issues/10188)
    * **PreserveTube** (`preservetube.com`): Public `/video/{id}` JSON API and HTML5 fallback; channel archives from `/channel/{id}/videos`. Request: [yt-dlp/yt-dlp#17540](https://github.com/yt-dlp/yt-dlp/issues/17540)
    * **Plurk** (`plurk.com`): Parse post-page `plurk` JSON for `video.plurk.com` MP4/HLS with the `verify` token. Request: [yt-dlp/yt-dlp#15679](https://github.com/yt-dlp/yt-dlp/issues/15679)
    * **Proko** (`proko.com`): Public `/api/lessons` and `/api/videos` JSON for YouTube/Vimeo lesson hosts; `/api/courses` playlists. Request: [yt-dlp/yt-dlp#9508](https://github.com/yt-dlp/yt-dlp/issues/9508)
    * **PromoDJ** (`promodj.com`): Parse `CORE.Player` JSON for prelisten/download MP3 and H.264 video. Request: [yt-dlp/yt-dlp#8721](https://github.com/yt-dlp/yt-dlp/issues/8721)
    * **PutlockerDigital** (`www2.putlocker.digital`): Watch-page JWPlayer `?number=` JSON for loadshare.org MP4/HLS. Request: [yt-dlp/yt-dlp#11365](https://github.com/yt-dlp/yt-dlp/issues/11365)
    * **QloveR** (`qlover.jp`): Public `api.qlover.jp/fc` Sheeta video_pages, session-id HLS, and CloudFront-cookie audio content_access. Request: [yt-dlp/yt-dlp#10260](https://github.com/yt-dlp/yt-dlp/issues/10260)
    * **QosVideos** (`qosvideos.com`): Schema.org VideoObject `contentURL` MP4 (Clean Tube player iframe fallback). Request: [yt-dlp/yt-dlp#8478](https://github.com/yt-dlp/yt-dlp/issues/8478)
    * **QuartierRouge** (`quartier-rouge.be`): Video.js HLS (`a.qr.be`) from public listing and profile pages. Request: [yt-dlp/yt-dlp#5831](https://github.com/yt-dlp/yt-dlp/issues/5831)
    * **RacingTV** (`racingtv.com`): Public `api.racingtv.com` on-demand JSON (client `API-KEY`) and HLS after the preroll token wait. Request: [yt-dlp/yt-dlp#17503](https://github.com/yt-dlp/yt-dlp/issues/17503)
    * **RadioCentral** (`radiocentral.ch`): Parse `window.__APOLLO_STATE__` show-segment AudioAssets (az-cdn MP3s) from podcast pages. Request: [yt-dlp/yt-dlp#8400](https://github.com/yt-dlp/yt-dlp/issues/8400)
    * **RadioCourtoisie** (`radiocourtoisie.fr`): WordPress `sr_playlist` REST plus Sonaar `playlist.json` MP3s (also `rc.fr`). Request: [yt-dlp/yt-dlp#6377](https://github.com/yt-dlp/yt-dlp/issues/6377)
    * **Rahatupu** (`rahatupu.net`): Schema.org VideoObject `contentUrl` MP4 (Clean Tube player iframe fallback). Request: [yt-dlp/yt-dlp#12300](https://github.com/yt-dlp/yt-dlp/issues/12300)
    * **RedziDzirdiLatviju** (`redzidzirdilatviju.lv`): Solr `/index` JSON for movies (Nimble HLS on `filmas.arhivi.lv`) and sound samples (archive MP3). Request: [yt-dlp/yt-dlp#15886](https://github.com/yt-dlp/yt-dlp/issues/15886)
    * **Rezka** (`rezka.ag`): Anubis PoW plus `initCDN*Events` / `ajax/get_cdn_series` voidboost HLS and MP4. Request: [yt-dlp/yt-dlp#17096](https://github.com/yt-dlp/yt-dlp/issues/17096)
    * **RidoMovies** (`ridomovies.tv`): Impersonate Cloudflare, follow Closeload JWPlayer embeds, and decode obfuscated HLS. Request: [yt-dlp/yt-dlp#13566](https://github.com/yt-dlp/yt-dlp/issues/13566)
    * **Sasflix** (`sasflix.ru`): Public `/api/web/topics/{id}` JSON plus HLS and progressive `/api/video` downloads. Request: [yt-dlp/yt-dlp#15373](https://github.com/yt-dlp/yt-dlp/issues/15373)
    * **SexBJCam** (`sexbjcam.com`): Impersonate Cloudflare and extract packed JWPlayer HLS from the playrecord.biz embed. Request: [yt-dlp/yt-dlp#15338](https://github.com/yt-dlp/yt-dlp/issues/15338)
    * **ShortMax** (`shorttv.live`): Nuxt `__NUXT_DATA__` HLS with custom per-segment AES-CBC. Request: [yt-dlp/yt-dlp#17230](https://github.com/yt-dlp/yt-dlp/issues/17230)
    * **ShoutTV** (`watch.shout-tv.com`): Guest DICE/IMG Gaming token (`dce.shout`) and v4 VOD/live HLS. Request: [yt-dlp/yt-dlp#11371](https://github.com/yt-dlp/yt-dlp/issues/11371)
    * **Showcamrips** (`showcamrips.com`): HTML5 MP4 from `play.php` with a showcamrips Referer. Request: [yt-dlp/yt-dlp#16822](https://github.com/yt-dlp/yt-dlp/issues/16822)
    * **Skai** (`skai.gr`): Player `var data` `episodemain` Wowza HLS (`videostream.skai.gr`). Request: [yt-dlp/yt-dlp#13456](https://github.com/yt-dlp/yt-dlp/issues/13456)
    * **Skland** (`skland.com`): Guest `zonai.skland.com` item API (Shumei device id + HMAC) for HLS. Request: [yt-dlp/yt-dlp#15545](https://github.com/yt-dlp/yt-dlp/issues/15545)
    * **Sleebi** (`sleebi.net`): Public `/v/API/{id}` metadata and PUT `/src` for hosted `videos.sleebi.eu` MP4s. Request: [yt-dlp/yt-dlp#15550](https://github.com/yt-dlp/yt-dlp/issues/15550)
    * **smotret.tv** (`smotret.tv`): Follow the channel player iframe and extract native HLS (`var streams`) or nested embeds. Request: [yt-dlp/yt-dlp#8899](https://github.com/yt-dlp/yt-dlp/issues/8899)
    * **Smule** (`smule.com`): Impersonate Cloudflare, RC4-decode `e:` media URLs from public `/p/{id}/json`, and download CDN MP4/M4A. Request: [yt-dlp/yt-dlp#10875](https://github.com/yt-dlp/yt-dlp/issues/10875)
    * **SNB** (`snb.ch`): Swisscom CSR webcast token plus public `/webcast/{id}` HLS from Research TV and Web TV pages. Request: [yt-dlp/yt-dlp#14562](https://github.com/yt-dlp/yt-dlp/issues/14562)
    * **song.link** (`song.link`): Next.js `pageData` listen links, preferring YouTube/SoundCloud/Audius/Audiomack/Bandcamp. Request: [yt-dlp/yt-dlp#13754](https://github.com/yt-dlp/yt-dlp/issues/13754)
    * **Sora** (`sora.com`): Public `backend/project_y/post` JSON (impersonate) for signed Azure MP4. Request: [yt-dlp/yt-dlp#14513](https://github.com/yt-dlp/yt-dlp/issues/14513)
    * **Spinitron** (`spinitron.com`): Playlist-page Ark `data-ark-start` HLS from `ark3.spinitron.com/ark2`; show pages list archived episodes. Request: [yt-dlp/yt-dlp#11401](https://github.com/yt-dlp/yt-dlp/issues/11401)
    * **Sponsr** (`sponsr.ru`): Parse Next.js post JSON and extract Kinescope HLS/MP4. Request: [yt-dlp/yt-dlp#14399](https://github.com/yt-dlp/yt-dlp/issues/14399)
    * **Spooncast** (`spooncast.net`): Public `{country}-api.spooncast.net/casts/{id}` JSON and CDN m4a. Request: [yt-dlp/yt-dlp#9590](https://github.com/yt-dlp/yt-dlp/issues/9590)
    * **SpotifyPodcasters** (`podcasters.spotify.com` / `creators.spotify.com`): Public `/pod/api/v3/episodes/{id}` JSON and CloudFront enclosure. Request: [yt-dlp/yt-dlp#9844](https://github.com/yt-dlp/yt-dlp/issues/9844)
    * **streamco:platform** (`api01-platform.stream.co.jp`): Parse Equipmedia `plt` player pages for JStream host/publisher/mid and extract HLS via `eq_meta` JSONP. Request: [yt-dlp/yt-dlp#13843](https://github.com/yt-dlp/yt-dlp/issues/13843)
    * **Streamgates** (`cplayer.streamgates.net`): Radiant Media Player `src.hls` DVR playlist. Request: [yt-dlp/yt-dlp#5720](https://github.com/yt-dlp/yt-dlp/issues/5720)
    * **StreamingCommunityz** (`streamingcommunityz`): Inertia `data-page` iframe to vixcloud HLS. Request: [yt-dlp/yt-dlp#14432](https://github.com/yt-dlp/yt-dlp/issues/14432)
    * **Streamruby** (`rubyvidhub.com`): Packed JWPlayer HLS from embed pages. Request: [yt-dlp/yt-dlp#14361](https://github.com/yt-dlp/yt-dlp/issues/14361)
    * **Streamster** (`streamster.tv`): MediaElement `video/youtube` source and player `videodata` YouTube embeds. Request: [yt-dlp/yt-dlp#14526](https://github.com/yt-dlp/yt-dlp/issues/14526)
    * **Streamtape** (`streamtape.com`): Reconstruct the obfuscated `get_video` MP4 URL from player JS. Request: [yt-dlp/yt-dlp#16770](https://github.com/yt-dlp/yt-dlp/issues/16770)
    * **Stuff** (`stuff.co.nz`): Public `/api/v1.0/stuff/story/{id}` JSON; Brightcove player or hosted HLS/MP4. Request: [yt-dlp/yt-dlp#14961](https://github.com/yt-dlp/yt-dlp/issues/14961)
    * **Sync** (`sync.com`): Public share `linkpathlist`/`pathdata` with PBKDF2+AES-GCM key unwrap and RSA-signed compat download. Request: [yt-dlp/yt-dlp#16598](https://github.com/yt-dlp/yt-dlp/issues/16598)
    * **Telegraph** (`telegraph.co.uk`): Impersonate Edge and extract particle iframe `window.videos` MP4/HLS. Request: [yt-dlp/yt-dlp#10291](https://github.com/yt-dlp/yt-dlp/issues/10291)
    * **TeraBox** (`terabox.app`): Impersonate, `/share/list` metadata, HMAC-SHA1 signed `/share/streaming.m3u8` HLS. Request: [yt-dlp/yt-dlp#10492](https://github.com/yt-dlp/yt-dlp/issues/10492)
    * **ThotDeep** (`thotdeep.com`): Decode JWPlayer `data-source` (pad, reverse, base64) and download single-use HLS. Request: [yt-dlp/yt-dlp#10746](https://github.com/yt-dlp/yt-dlp/issues/10746)
    * **Thothub** (`thothub.to`): KVS `kt_player` flashvars and license-decoded `get_file` MP4s. Request: [yt-dlp/yt-dlp#13133](https://github.com/yt-dlp/yt-dlp/issues/13133)
    * **Threads** (`threads.net` / `threads.com`): Parse logged-out `data-sjs` Relay JSON for `video_versions` and DASH. Request: [yt-dlp/yt-dlp#7523](https://github.com/yt-dlp/yt-dlp/issues/7523)
    * **ThreeNow** (`threenow.co.nz`): Live channels from the public `now-api.fullscreen.nz` `live-epg` HLS. Request: [yt-dlp/yt-dlp#17082](https://github.com/yt-dlp/yt-dlp/issues/17082)
    * **TimesRadio** (`thetimes.com`): HTML5 catch-up MP3 (Omny) and live AAC stream from Times Radio pages; impersonate for the device-check interstitial. Request: [yt-dlp/yt-dlp#17253](https://github.com/yt-dlp/yt-dlp/issues/17253)
    * **Tipeee** (`tipeee.com` / `tipeee.fr`): Public news-post `api.tipeee.com` JSON and YouTube/Vimeo embed URLs. Request: [yt-dlp/yt-dlp#8465](https://github.com/yt-dlp/yt-dlp/issues/8465)
    * **TreffDarc** (`treff.darc.de`): BigBlueButton `metadata.xml` plus public webcam/deskshare WebM/MP4. Request: [yt-dlp/yt-dlp#11372](https://github.com/yt-dlp/yt-dlp/issues/11372)
    * **TuckerCarlson** (`tuckercarlson.com`): Impersonate Cloudflare, then JSON-LD `contentUrl` Cloudflare Stream HLS/DASH. Request: [yt-dlp/yt-dlp#9169](https://github.com/yt-dlp/yt-dlp/issues/9169)
    * **TVAsahiDouga** (`douga.tv-asahi.co.jp`): Episode-page `window.app` Falcor metadata and Brightcove HLS (`ovp_video_id`) with JP geo-bypass. Request: [yt-dlp/yt-dlp#14947](https://github.com/yt-dlp/yt-dlp/issues/14947)
    * **TVMonaco** (`tvmonaco.com`): Okast `/api/media/v7/media` metadata and AES-128 HLS from `/api/offer/v4/media/{uuid}/url`. Request: [yt-dlp/yt-dlp#11687](https://github.com/yt-dlp/yt-dlp/issues/11687)
    * **TVTropes** (`tvtropes.org`): Impersonate Cloudflare and extract Bunny HLS from video-example data attributes. Request: [yt-dlp/yt-dlp#17106](https://github.com/yt-dlp/yt-dlp/issues/17106)
    * **Udio** (`udio.com`): Public `/api/songs` JSON for `song_path` MP3 and `video_path` MP4. Request: [yt-dlp/yt-dlp#10045](https://github.com/yt-dlp/yt-dlp/issues/10045)
    * **UKDevilz** (`ukdevilz.com`): Impersonate Cloudflare and extract JWPlayer `window.playlist` MP4 sources. Request: [yt-dlp/yt-dlp#14166](https://github.com/yt-dlp/yt-dlp/issues/14166)
    * **UpRide** (`upride.cc`): Impersonate Cloudflare, then JSON-LD `contentURL` original upload plus Cloudflare Stream iframe HLS/DASH. Request: [yt-dlp/yt-dlp#7858](https://github.com/yt-dlp/yt-dlp/issues/7858)
    * **USNewsOn** (`usnewson.com`): Video.js `pllrc` onestream API (`pro.usnlive.com/api/stream`) and direct HLS. Request: [yt-dlp/yt-dlp#6985](https://github.com/yt-dlp/yt-dlp/issues/6985)
    * **Veev** (`veev.to`): Decode the player `fc` token and `/dl?op=player_api` source URL. Request: [yt-dlp/yt-dlp#10092](https://github.com/yt-dlp/yt-dlp/issues/10092)
    * **Videas** (`videas.fr`): Player `data-embed` JSON and CDN HLS. Request: [yt-dlp/yt-dlp#7786](https://github.com/yt-dlp/yt-dlp/issues/7786)
    * **VidMoly** (`vidmoly.to`): Canonical `vidmoly.biz` embed JWPlayer HLS (also `.me`/`.net`). Request: [yt-dlp/yt-dlp#9689](https://github.com/yt-dlp/yt-dlp/issues/9689)
    * **Viggle** (`viggle.ai`): Public `/api/share/video-task` JSON (impersonate) for signed `assets.viggle.ai` MP4. Request: [yt-dlp/yt-dlp#13657](https://github.com/yt-dlp/yt-dlp/issues/13657)
    * **VillageSexVideos** (`villagesexvideos.com`): Impersonate Cloudflare, then schema `contentURL` MP4 (Clean Tube player iframe fallback). Request: [yt-dlp/yt-dlp#7033](https://github.com/yt-dlp/yt-dlp/issues/7033)
    * **VMware** (`vmware.com`): Brightcove player IDs from `/video/` and Explore library pages via `/get-st`. Request: [yt-dlp/yt-dlp#10881](https://github.com/yt-dlp/yt-dlp/issues/10881)
    * **WCOStream** (`wcostream.tv`): Impersonate Cloudflare, map embed `file=` to `getvidlink.php` (`cizgi`/`neptun`) tokens, and download `getvid` MP4s. Request: [yt-dlp/yt-dlp#13987](https://github.com/yt-dlp/yt-dlp/issues/13987)
    * **wcvb** (`wcvb.com`): Next.js `voltronArticle` Hearst Digital Studios MP4 transcodings. Request: [yt-dlp/yt-dlp#10548](https://github.com/yt-dlp/yt-dlp/issues/10548)
    * **WedoTV** (`wedotv.com`): Public `/api/player.get_video.php` HLS from the page `data-video-id`. Request: [yt-dlp/yt-dlp#14221](https://github.com/yt-dlp/yt-dlp/issues/14221)
    * **Welt** (`welt.de`): `WeltVideoPlayer` hydration JSON progressive MP4s and HLS. Request: [yt-dlp/yt-dlp#7513](https://github.com/yt-dlp/yt-dlp/issues/7513)
    * **Xbox** (`xbox.com`): Microsoft displaycatalog `CMSVideos` HLS/DASH store trailers. Request: [yt-dlp/yt-dlp#13591](https://github.com/yt-dlp/yt-dlp/issues/13591)
    * **Xcadr** (`xcadr.tv`): KVS `kt_player` `flashvars` and license-decoded `get_file` MP4s; celeb/movie listings as playlists. Request: [yt-dlp/yt-dlp#6362](https://github.com/yt-dlp/yt-dlp/issues/6362)
    * **XFetishTube** (`x-fetish.tube`): KVS `kt_player` config (randomized JS object) and license-decoded `get_file` MP4s. Request: [yt-dlp/yt-dlp#16623](https://github.com/yt-dlp/yt-dlp/issues/16623)
    * **XiaoHeiMi** (`xiaoheimi.net`): Impersonate Cloudflare and extract MacCMS `player_aaaa` HLS. Request: [yt-dlp/yt-dlp#5625](https://github.com/yt-dlp/yt-dlp/issues/5625)
    * **XPicVid** (`xpicvid.com`): Impersonate Cloudflare and extract DPlayer quality MP4s. Request: [yt-dlp/yt-dlp#15279](https://github.com/yt-dlp/yt-dlp/issues/15279)
    * **Xumo** (`play.xumo.com`): Public `valencia-app-mds.xumo.com` asset JSON for HLS/DASH VOD and series playlists. Request: [yt-dlp/yt-dlp#15643](https://github.com/yt-dlp/yt-dlp/issues/15643)
    * **XXXTik** (`xxxtik.com`): Public DigitalOcean `/post/{uuid}` JSON and CDN HLS (`p5rn.com` / `xcdn.tv`). Request: [yt-dlp/yt-dlp#6224](https://github.com/yt-dlp/yt-dlp/issues/6224)
    * **youku:tv** (`youku.tv`): Impersonate Chrome, then mtop UPS `appinfo.get` (ccode 0597) HLS. Request: [yt-dlp/yt-dlp#8058](https://github.com/yt-dlp/yt-dlp/issues/8058)

* **Extractor fixes** (verified on live sites where possible):
    * **20min**: Extract videos from the Unity API instead of the old podcast URLs
    * **abcnews**: Read the current `story.story` JSON instead of everscroll
    * **abc:iview**: Use the v3 video API and raise geo/login when unplayable
    * **allocine**: Extract Dailymotion videos via `DailymotionIE`
    * **bunnycdn**: Fall back to `playlist.m3u8` when JSON-LD is missing
    * **cliprs**: Extract Ring Publishing embeds
    * **cspan**: Fall back to JSON-LD / m3u8 when player JS is blocked
    * **cu.ntv.co.jp**: Raise geo-restriction when CloudFront / Streaks block playback outside Japan
    * **cybrary**: Call the catalog API without requiring a login token
    * **dailywire**: Use the GraphQL API instead of Next.js page data
    * **dangalplay**: Extract public Akamai HLS from `smart_url` without login
    * **daum**: Extract the current Kakao/Daum VOD player instead of the dead tvpot embed
    * **daystar**: Read Lightcast `configUrl` from the player iframe (including `/live/` URLs)
    * **dfb**: Follow YouTube embeds and match `dfb.de` news video URLs
    * **dhm**: Support journal articles and JWPlayer/HLS when the XSPF playlist is gone
    * **digiview**: Send an `Origin` header on the player POST
    * **doodstream**: Impersonate the browser and join relative `pass_md5` URLs
    * **douyu**: Sign streams with Node instead of PhantomJS
    * **dplay**: Use Disco playback v3
    * **drtalks**: Follow BunnyCDN embeds from Next.js v13 instead of Brightcove
    * **drtuber**: Use HTTPS `player_config_json` and tolerate missing files
    * **dtube**: Support `/watch/` URLs and current IPFS/media hosts
    * **dumpert**: Use the HTTPS API and impersonate the browser
    * **duoplay**: Register sessions on `sts.euddn.net`
    * **ebaumsworld**: Parse the current HTML/JSON player instead of the old XML API
    * **elpais**: Fall back to JSON-LD media, then a YouTube embed, when `url_cache` is missing
    * **epicon**: Extract HLS from the page when `ajaxplayer` returns 405 or has no trailer cid
    * **erocast**: Impersonate the browser
    * **ettutv**: Match live/videos player URLs and extract current streams
    * **fancode**: Support current GraphQL / public video pages
    * **faz**: Follow YouTube embeds
    * **filmweb**: GraphQL clip query and YouTube embeds; broader article URLs
    * **flickr**: Impersonate the browser when fetching the API key
    * **fptplay**: Sign the v7.1 API
    * **freespeech**: Zype embeds, live-tv URLs, and browser impersonation
    * **freetv**: Use the current playback API instead of WordPress admin-ajax
    * **funker530**: Follow BunnyCDN / current embeds instead of Rumble-only
    * **gamedevtv**: Extract public course preview media via sales-data / BunnyCDN without login
    * **gamespot**: JW Platform embeds and slug URLs
    * **gamestar**: Dailymotion player config (impersonate Firefox)
    * **gazeta**: Extract current article video embeds
    * **gedidigital**: Broader lastampa / repubblica video URLs
    * **giantbomb**: JW Platform on current show/video slugs
    * **glide**: Nested share path IDs
    * **globalplayer:live**: Fetch the stream from the guacamole playables API
    * **godtube**: Schema.org `contentUrl` instead of player XML
    * **gofile**: Sign `X-Website-Token` from `wt.obf.js` and download all folder files (any type) with the `accountToken` cookie
    * **gopro**: Fetch the download URL from the JWT `medium_id`
    * **gotostage**: New Goto contentservice API hosts
    * **hbo**: Current HBO.com video/embed JSON instead of the old XML player
    * **heise**: Targetvideo `<a-video>` embeds
    * **historicfilms**: OG video URL and `?reel=` search URLs
    * **hotnewhiphop**: YouTube embeds instead of the old `data-path` player
    * **huajiao**: `feed/getFeedInfo` API
    * **hungama**: Playable API with web/free devices
    * **icareus**: `/video/details/` and `/event/details/` URLs
    * **ign**: Tolerate missing `videoId` and extra m3u8 paths
    * **ilpost**: Next.js episode data and podcast path URLs
    * **imdb**: GraphQL `VideoPlayback` API
    * **indavideo**: Referer + JSONP callback on `playerHandler`
    * **iqiyi**: Current IQ/iQIYI playback (bid quality tags and signed play URLs)
    * **islamchannel**: VOD paths and a fallback stream URL
    * **ixigua**: Decode play URLs and fetch with a Googlebot UA
    * **jable**: Impersonate the browser
    * **jeuxvideo**: Dailymotion embeds (impersonate)
    * **jixie**: Kompas `jixie-stream` API
    * **joj**: `play.joj.sk` player/videos URLs
    * **jove**: Current video/HLS pages
    * **kakao**: Raise an expected error that KakaoTV shut down on 2026-06-30
    * **kankanews**: Current page media JSON
    * **khanacademy**: Fetch `published-content-version` instead of a hardcoded hash
    * **kicker**: RSS media feeds (and optional `www`)
    * **kickstarter**: Impersonate the browser to avoid 403s
    * **kinopoisk**: Discovery widget JSON instead of `ott-widget`
    * **ku6**: `video/detail?id=` pages
    * **kukululive**: `live.player.php` `getStreamAddr` API
    * **kuwo**: HTTPS antiserver + current song pages
    * **laracasts**: Inertia `data-page` JSON
    * **leeco**: Guard missing `playstatus`
    * **lefigaro**: JW Platform on non-embed video URLs
    * **lemonde**: Dailymotion / YouTube / Digiteka provider map
    * **lifenews**: Next.js `pData` VIDEO blocks and `/p/` URLs
    * **likee**: Raise an expected error that public web pages are gone (app-only)
    * **listennotes**: Impersonate the browser
    * **litv**: Authenticated `get-urls` API
    * **livejournal**: Current video JSON
    * **loc**: `media.loc.gov` IDs and loc JSON media
    * **locipo**: Direct `video_file_name` when the Streaks API key is gone
    * **maoritv**: maoriplus.co.nz, live/movie URLs, and a dynamic Brightcove account
    * **mave**: `cdn.mave.digital` storage
    * **mellowfan**: Fall back to the public movies API and `url_public` HLS when the authenticated detail API requires login
    * **meipai**: Signed media API instead of `encodeURIComponent` m3u8 on the page
    * **metacritic**: JW Platform on movie/game/tv pages
    * **microsoft:medius**: Extract HLS manifests when Smooth Streaming is gone
    * **minds**: v2 entities API
    * **mirrorcouk**: JSON-LD media
    * **mit**: YouTube embeds on current OCW course URLs
    * **mocha**: Current mocha.com.vn API
    * **MovingImage**: Fall back to a Wayback Machine snapshot when AWS WAF captcha blocks the catalogue page
    * **mtg**: Use the TV3 Play/GO3 products API (via play.tv3.lt, tenant AVOD_*) instead of the dead playapi.mtgx.tv; download the public preview MP4 when full streams are DRM
    * **murrtube**: Current app JSON
    * **museai**: skiv.com rebrand
    * **musescore**: New auth token + impersonate
    * **mx3**: Range request for filesize
    * **myspass**: CDN77 media URLs and current clip/folge paths
    * **myvidster**: Follow YouTube (and other) embeds from current video pages
    * **n-joy**: JSON-LD / `data-config` ARD player media
    * **n-tv.de**: Extract Next.js player streams and current `-id` video URLs
    * **nba**: Extract public team-site WordPress MP4s from Next.js `videoAssets`
    * **nbcsports**: Extract ThePlatform JWPlayer links when the old vplayer embed is gone
    * **nbcolympics**: Mark VOD as US geo-restricted (ThePlatform; X-Forwarded-For is ignored)
    * **netapp**: Extract YouTube embeds from current video pages (Brightcove API gone); impersonate for Akamai
    * **netzkino**: Raise geo-restriction when CloudFront blocks the PMD CDN (DE/AT/CH; X-Forwarded-For is ignored)
    * **newgrounds**: Solve NG Guard argon2id/sha256 proof-of-work; update the audio player media URL regex
    * **nhl.com**: Extract Brightcove embeds from current video pages (bamcontent API gone)
    * **ninenews**: Parse Brightcove id/account from page markup
    * **nintendo**: Read Direct metadata from Next.js Apollo state instead of the dead GraphQL API
    * **noice**: Fetch catalog-api HLS/MP4 with the page guest token
    * **noodlemagazine**: Impersonate the browser
    * **nosnl**: Treat nested `/video/` article URLs as videos
    * **nova**: Fall back to a Wayback Machine snapshot and OTT preview MP4s when the live page is blocked
    * **noz**: Follow 3Q SDN embeds on current `/video/` article pages
    * **npo**: Use the NPO Start `player-token` and `npoplayer` stream-link APIs
    * **npr**: Fall back to JSON-LD JWPlayer media when the query API is blocked
    * **nubilesporn**: Impersonate the browser, prime a tour session to bypass Turnstile, and extract public shorts MP4s
    * **oftv**: Extract HLS from the current `api.of.tv` player instead of Zype
    * **ondemandchina**: Use US/CA X-Forwarded-For on the ODC playback API
    * **onet.pl**: Extract PulseEmbed JSON-LD and Ring Publishing MP4 instead of the old CKM API
    * **onet.tv**: Map clip URLs onto the video.onet.pl successor and extract via OnetPl
    * **orf:on**: Raise geo-restriction when sources are empty
    * **owncloud**: Build Nextcloud public download URLs (`/s/{id}/download` and folder `path`/`files`) after sciebo's ownCloud-to-Nextcloud migration
    * **packtpub**: Use the subscription products API for public S3 preview MP4s
    * **paramountpressexpress**: Raise geo-restriction when Brightcove press pages return location-not-allowed (X-Forwarded-For is ignored); YouTube-hosted press videos still extract
    * **parler**: Use the public v4 posts API for app/play post URLs
    * **pbs**: Guard against missing `video_info` and title
    * **pbskids**: Extract Next.js `/videos/watch/` pages and PBS URS HLS/MP4
    * **peekvids**: Read the numeric ID from the thumbnail URL and fall back to the page HLS source
    * **peer.tv**: Read JSON-LD `contentUrl` MP4s and match `/video/` slug URLs
    * **performgroup**: Use the DAZN feeds VOD API instead of the dead Perform Feeds ep3 host
    * **photobucket**: Extract sharing-link videos via GraphQL instead of the old `Pb.Data.Shared` page JSON
    * **pinkbike**: Impersonate the browser and extract current Video.js sources
    * **playtvak**: Call the public `servix.idnes.cz` player API and match current iDNES.tv URLs
    * **playvids**: Read the numeric ID from `get_related_videos` when the player has no `data-id`
    * **plutotv**: Match current `/movies/` and `/shows/` VOD URLs
    * **polsatgo**: Use the Polsat Box Go `pbg` portal after Polsat Go shutdown; raise login when playback is denied
    * **podbayfm**: Impersonate the browser
    * **podomatic**: Use the public v2 episode API and enclosure MP3s instead of the dead embed_params JSON
    * **popcorntimes**: Follow public trailer YouTube/Dailymotion embeds; raise geo-restriction for DACH-only feature films (X-Forwarded-For is ignored)
    * **popcorntv**: Match `/streaming/` URLs, fetch via `www` to avoid the apex's expired TLS cert, and follow YouTube trailer embeds
    * **pornbox**: Extract public trailer streams when the full scene requires login
    * **pornotube**: Use the site `/deliver` HLS endpoint instead of the dead AEBN clips API
    * **pornovoisines**: Extract Revma pack MP4s and JSON-LD trailers instead of the dead settings API
    * **pornoxo**: Impersonate the browser and extract HLS from `playerConfig`
    * **pr0gramm**: Request SFW-only API flags unless logged in
    * **premiershiprugby**: Follow YouTube highlight embeds from the article CMS; keep StreamAMG HLS for native full matches
    * **presstv**: Extract JWPlayer HLS and preview MP4 from current article pages; match presstv.co.uk
    * **projectveritas**: Extract Mux playback from Next.js App Router instead of Gatsby page-data
    * **prx**: Fall back to public Exchange piece pages and signed MP3 streams when the CMS API requires authorization
    * **puhutv**: Extract current Akamai HLS `master.m3u8` streams from the video API
    * **qdance**: Extract public Q-dance Radio from StreamTheWorld when Network VOD requires login
    * **r7**: Read Fusion `globalContent` streams on current video pages; scrape `player.r7.com` HTML when `player-api` is gone
    * **radlive**: Extract HLS from the 12core GraphQL API and match `/watch/` feature/episode URLs
    * **radiofrance:live**: Use public HLS streams instead of `/api/live`
    * **radiojavan**: Use the public play.radiojavan.com video API instead of the old `video_host` page scrape
    * **radiokapital**: Use the `api.radiokapital.pl` WordPress REST API
    * **rds**: Read Jasper embed / Fusion Axis ids on current Arc video pages
    * **redbull**: Use GraphQL `v1:pageConfig` and `api-player.redbull.com` HLS instead of the dead crepo GraphQL / `v1:hero` schema
    * **redbulltv**: Play `api.redbull.tv` products via rrn content IDs and `dms.redbull.tv` HLS
    * **reuters**: Read Fusion `globalContent` HLS on current `/video/watch/` pages (impersonate for DataDome)
    * **rockstargames**: Read v4 player JSON (`/v4/{id}/data/{locale}.json`) instead of the dead get-video.json API
    * **rozhlas**: Resolve slugs via the search API; unwrap single-item station playlists
    * **rte:radio**: Extract current `/radio/.../episodes/` catch-up from getplaylist (HLS and Omny MP3)
    * **rtbf**: Use the Auvio BFF and anonymous RedBee play for current `auvio.rtbf.be` URLs
    * **rtl.lu**: Extract ReplayVideo HLS and ReplayAudio MP3 from current Brightspot/Next.js article pages
    * **rtl.nl**: Use the RTL XL token and watch/play v2 APIs for current video UUIDs (FairPlay/Widevine DRM)
    * **rtp**: Fall back to webpage player URLs when the mobile guest token API 404s
    * **rtrfm**: Read restream episode metadata from the current show page instead of the removed `.playShow` JS
    * **ruv.is:spila**: POST the GraphQL program query instead of GET
    * **rumble**: Impersonate the browser for embedJS, video pages, and media downloads
    * **Ruutu**: Use the public MCC media API instead of the retired gatling XML cache
    * **samplefocus**: Parse SampleHero React JSON and JSON-LD AudioObject instead of removed hidden form fields
    * **sangiin**: Extract HLS from the MediaSP player instead of the old `videopath` variable
    * **sbs**: Fall back to the public FOS `mpx/video/stream` HLS API when `video_smil` is gone
    * **sbs.co.kr**: Use the current `apis.sbs.co.kr/play-api` host instead of the dead `api.play.sbs.co.kr` endpoint
    * **screencastomatic**: Extract ScreenPal `player/stream` MP4s after the Screencast-O-Matic rebrand
    * **scrolller**: Use the current `api.scrolller.com/admin` GraphQL `getPost` query
    * **sexu**: Use `/api/video-info` (HLS + MP4) and JSON-LD instead of the old JWPlayer setup
    * **showroom**: Use the public room API instead of Nuxt + login cookie
    * **sky:news**: Impersonate the browser and extract Brightcove IDs from the video sitemap / iframe widget when Akamai blocks the page
    * **sky:sports**: Fetch a Condatis Brightcove JWT and match current `/{sport}/video/` clip URLs
    * **slideshare**: Extract public slide images from the GraphQL API after the Next.js rebrand
    * **slutload**: Impersonate the browser and extract HLS from CamSoda `/porn/video/` preloaded JSON
    * **spankbang**: Parse `stream_data` and current `data-testid` video-page metadata
    * **sport5**: Extract Akamai HLS from current article player embeds
    * **sporteurope**: Use the public asset and web-player APIs for signed Mux HLS
    * **smotrim**: Use the `player-api.smotrim.ru` v1 API instead of the old iframe `datavideo` JSON
    * **softwhiteunderbelly**: Treat anonymous VHX `_session` cookies as logged-out and require a subscribed account
    * **sr:mediathek**: Join relative ARD player collection URLs
    * **startrek**: Parse Next.js App Router flight data instead of `__NEXT_DATA__`
    * **startv**: Call the DYG `video_info` API using the page `referenceId`
    * **stv:player**: Mark playback as UK geo-restricted (Brightcove CDN; X-Forwarded-For is ignored)
    * **sunporno**: Decode KVS `get_file` hashes on current `/v/` and `/embed/` pages
    * **sverigesradio**: Extract `playAudio` / episode audio from Next.js App Router data instead of the dead playerajax API
    * **sztvhu**: Follow YouTube embeds instead of the old media.sztv.hu VOD player
    * **t-online.de**: Extract Next.js / JSON-LD HLS (and CMAF HTTP) on current `/video/` URLs instead of the dead `tid_json_video` API
    * **tarangplus**: Use the catalog API and public preview HLS instead of the old SSR iframe
    * **tass**: Use the public TBP content API (impersonate) instead of JWPlayer sources
    * **tbs:newsdig**: Extract public Streaks HLS from NEWS DIG articles
    * **tele13**: Follow rudo.video (and YouTube) embeds instead of the old JWPlayer setup
    * **tele5**: Play VOD via the Aurora sonic API (`public.aurora.enhanced.live`, realm `de`) instead of disco-api dmaxde
    * **telequebec**: Extract Brightcove `ref:` media IDs from current `/regarder/` pages
    * **tfo**: Extract JWPlayer HLS from the episode API / watch-page player (geo-restricted to Canada; X-Forwarded-For is ignored)
    * **theguardian:podcast**: Extract audio URL and author from JSON-LD
    * **TheIntercept**: Follow YouTube/Vimeo embeds and native HTML5 video on current article pages
    * **theplatform**: Treat `link.theplatform.com` `/guid/` release URLs as SMIL instead of scraping a player page that now 302s to media
    * **thisamericanlife**: Parse playlist JSON for MP3/HLS instead of the old hardcoded stream path
    * **thisav**: Raise an expected error that thisav.com was seized by FANZA in 2025 and no longer hosts videos
    * **tiktok**: Googlebot headers on aweme detail
    * **tnaflix**: Impersonate the browser (including Empflix)
    * **toongoggles**: Use the OTTera API and embedded player HLS instead of the old numeric show API
    * **toypics**: Extract OvenPlayer / og:video MP4s from current `/u/{user}/{id}` pages
    * **trtworld**: Extract Next.js v13 CMS media (HLS/MP4) and YouTube fallbacks on current `/video/{slug}` URLs
    * **trunews**: Raise an expected error that trunews.com is a coming-soon landing page and no longer hosts videos
    * **tube8**: Extract playervars HLS/MP4 from current `/porn-video/` pages
    * **tubitv**: Raise geo-restriction when CloudFront redirects to gdpr.tubi.tv (X-Forwarded-For is ignored)
    * **tumblr**: Impersonate the browser
    * **TravelChannel**: Match `www.travelchannel.com` video URLs after `watch.` redirected
    * **tv2**: Use the Vimond content-discovery and play APIs instead of the dead Sumo REST API
    * **TV2DK**: Impersonate the browser to avoid HTTP 406 on regional TV 2 article pages
    * **TV5MONDE**: Extract information.tv5monde.com news videos from the player API / direct MP4; raise an expected error when old `/tv/video` URLs redirect to DRM-protected TV5MONDE+
    * **tvigle**: Resolve current `/video/` pages from Next.js data and the cloud play API
    * **tvn24**: Extract JSON-LD VideoObject MP4s on current `/...-vd` pages instead of the old data-quality player
    * **tvp**: Fall back to the original TVPlayer object id when retired portals such as swipeto.pl 301 to the VOD homepage
    * **tvw**: Impersonate the browser
    * **tweakers**: Follow YouTube embeds from `YouTubePlayer.init` (impersonate, DPG privacy gate)
    * **twitter:amplify**: Extract current `video.twimg.com` Amplify VMAP instead of the decommissioned `amp.twimg.com` player
    * **unistra**: Extract HTML5 `vod-stream.di.unistra.fr` MP4s instead of the dead Flash `vod-flash.u-strasbg.fr` host
    * **unity**: Follow YouTube embeds on current Unity Learn tutorial pages (including `learn.unity.com`)
    * **urort**: Extract S3 `data-trackurl` from current `/track/` pages
    * **usatoday**: Extract Gannett CDN HLS from `data-c-vpd` instead of Brightcove
    * **ustream**: Fetch IBM Video Streaming HLS over HTTPS UMS when `media_urls` is empty
    * **ustudio:embed**: Fetch embed `config.json` over HTTPS and read `image_url` posters
    * **vqq:video**: Fall back to the union / float_vinfo2 APIs when pinia/OG metadata is gone
    * **videa**: Support player URLs with an `f=` parameter
    * **viddler**: Use the current public `/api/videos/` JSON and Mux HLS instead of the retired v2 playback API
    * **viewsb**: Raise an expected error that viewsb.com is a ParkLogic parking page and StreamSB no longer hosts videos
    * **Viqeo**: Parse `window.DATA` and follow VK-hosted `video_ext` media
    * **viu**: Extract public `hq.viu.com` trailer MP4s; raise geo-restriction when OTT APIs block this country (X-Forwarded-For is ignored)
    * **vevo**: Use the GraphQL TV API instead of the dead apiv2 REST API
    * **vice**: Extract article videos from the WordPress REST API (HTML5, YouTube, Vimeo)
    * **vodplatform**: Impersonate the browser on current KWIKmotion embed pages
    * **voxmedia**: Follow Volume embeds from JSON-LD / `volume.vox-cdn.com`, then YouTube
    * **vrt**: Parse `mediaReference` from Next.js / JSON-LD when `vrtvideo` is gone
    * **vrtmax**: Query EpisodePage player/JSON-LD GraphQL after the `episode` field was removed
    * **vtm**: Pass the DPG privacy gate and impersonate the browser to extract public mychannels clips
    * **vtv**: Extract HLS from classic `data-vid` and shorts `data-file` CDN paths
    * **weiqitv**: Extract `/v/` Clappr MP4 and `/l/` NetEase live HLS; raise login when `_vu` is withheld
    * **wevidi**: Raise an expected error when Cloudflare 302s the entire domain to YouTube; fall back to a YouTube embed when WVPlayer is missing
    * **wimbledon**: Extract current `/video/{slug}` pages via GraphQL and Adobe Scene7 HLS; keep Brightcove for legacy `/video/media/` IDs
    * **WorldStarHipHop**: Extract JSON-LD MP4s from current `/videos/{id}/{slug}` pages
    * **wppilot**: Load the guest channel list from the public API instead of the old Gatsby CDN page-data; raise geo-restriction when guest streams return `user_outside_eu` (X-Forwarded-For is ignored)
    * **wwe**: Read Drupal 10 `drupal-settings-json` instead of the old `Drupal.settings` JS
    * **xanimu**: Impersonate the browser to bypass Cloudflare and read JSON-LD metadata
    * **xfileshare**: Match current Uqload TLDs (`uqload.vc` and related mirrors) after `uqload.com` started redirecting
    * **xinpianchang**: Read Next.js `_next/data` instead of WAF-blocked article HTML; send Referer on media CDN requests
    * **XMinus**: Reconstruct xmst.cc `/dl/minus` URLs from the current x-minus.pro player after x-minus.org expired
    * **yandexdisk**: Support password-protected public files (`--video-password`)
    * **yandexvideo**: Read preview player JSON from `<noframes>` and follow the host video URL
    * **yapfiles**: Parse the current yaplayer load URL and `file`/`file_hd` from the API instead of the old `player.init` playlist
    * **younow**: Raise an expected error that live playback is WebRTC (Props SFU) and that public HLS/moments are gone
    * **zetland**: Extract `storyServer` audio from Next.js App Router flight data
    * **zingmp3**: Sign API requests with the current app `version` and only the documented params

* **Ported live-verified upstream PRs** that had not been merged yet: TED `videoPlayerData`, HearThisAt API host, VGTV HTTPS API, RTVE Play clan URLs, and xHamster sources/pagination

* **Extractor internals**:
    * `subs_list_to_dict` copies entries before mutating them
    * Skip non-numeric `age_limit` test values when listing extractors so `make_supportedsites` does not crash

* **Testing and developer workflow**:
    * Offline coverage and extractor/CLI fixture tests
    * Live byte-fetch tests from confirmed public URLs, plus many live extractor test updates (`live-site-status.csv`)
    * Node as the JS runtime for download tests
    * Skip dead / geo / login tests and refresh stale sample metadata
    * `make_changelog` attributes fork commits to the git author and `CrimsonGlory/yt-ai`
    * [Development Docker workflow](https://github.com/CrimsonGlory/yt-ai/commit/13d780d260672007c07b37e4b5060a06c27d5b15) (`docker/Dockerfile` + compose) to run yt-ai and the offline suite in a container
    * `release.sh` crontab helper: dispatch the GitHub `Release` workflow only when `master` has commits after the latest GitHub release (no nightly/stable channel)

See [commits](https://github.com/CrimsonGlory/yt-ai/commits) for the full list of changes

### Differences in default behavior

Relative to **yt-dlp**:

* The command name and release binaries are `yt-ai` instead of `yt-dlp`
* Config files are `yt-ai.conf` and live under `yt-ai` directories (`${XDG_CONFIG_HOME}/yt-ai`, `${APPDATA}/yt-ai`, `~/.yt-ai`, `/etc/yt-ai`). See [CONFIGURATION](#configuration)
* Cache defaults to `${XDG_CACHE_HOME}/yt-ai` instead of `${XDG_CACHE_HOME}/yt-dlp`
* Plugins are loaded from `yt-ai` config folders and `yt-ai-plugins` (not `yt-dlp-plugins`). See [plugins](#plugins)
* The PyPI package is [`yt-ai`](https://pypi.org/project/yt-ai); embedding still uses `import yt_dlp`
* Sites yt-dlp refused as piracy, and extractors it marked currently broken, are enabled again
* AI / LLM contributions are required (see [`.NO_HUMAN`](.NO_HUMAN/README.md))

CLI defaults (format selection, output template, Python version, and so on) otherwise match yt-dlp. The following differences from youtube-dl / youtube-dlc, and the `--compat-options` that revert them, are inherited from yt-dlp:

* yt-ai supports only [Python 3.10+](## "Windows 8"), and will remove support for more versions as they [become EOL](https://devguide.python.org/versions/#python-release-cycle); while [youtube-dl still supports Python 2.6+ and 3.2+](https://github.com/ytdl-org/youtube-dl/issues/30568#issue-1118238743)
* The options `--auto-number` (`-A`), `--title` (`-t`) and `--literal` (`-l`), no longer work. See [removed options](#Removed) for details
* `avconv` is not supported as an alternative to `ffmpeg`
* yt-ai stores config files in slightly different locations to youtube-dl. See [CONFIGURATION](#configuration) for a list of correct locations
* The default [output template](#output-template) is `%(title)s [%(id)s].%(ext)s`. There is no real reason for this change. This was changed before yt-ai was ever made public and now there are no plans to change it back to `%(title)s-%(id)s.%(ext)s`. Instead, you may use `--compat-options filename`
* The default [format sorting](#sorting-formats) is different from youtube-dl and prefers higher resolution and better codecs rather than higher bitrates. You can use the `--format-sort` option to change this to any order you prefer, or use `--compat-options format-sort` to use youtube-dl's sorting order. Older versions of yt-ai preferred VP9 due to its broader compatibility; you can use `--compat-options prefer-vp9-sort` to revert to that format sorting preference. These two compat options cannot be used together
* The default format selector is `bv*+ba/b`. This means that if a combined video + audio format that is better than the best video-only format is found, the former will be preferred. Use `-f bv+ba/b` or `--compat-options format-spec` to revert this
* Unlike youtube-dlc, yt-ai does not allow merging multiple audio/video streams into one file by default (since this conflicts with the use of `-f bv*+ba`). If needed, this feature must be enabled using `--audio-multistreams` and `--video-multistreams`. You can also use `--compat-options multistreams` to enable both
* `--no-abort-on-error` is enabled by default. Use `--abort-on-error` or `--compat-options abort-on-error` to abort on errors instead
* When writing metadata files such as thumbnails, description or infojson, the same information (if available) is also written for playlists. Use `--no-write-playlist-metafiles` or `--compat-options no-playlist-metafiles` to not write these files
* `--add-metadata` attaches the `infojson` to `mkv` files in addition to writing the metadata when used with `--write-info-json`. Use `--no-embed-info-json` or `--compat-options no-attach-info-json` to revert this
* Some metadata are embedded into different fields when using `--add-metadata` as compared to youtube-dl. Most notably, `comment` field contains the `webpage_url` and `synopsis` contains the `description`. You can [use `--parse-metadata`](#modifying-metadata) to modify this to your liking or use `--compat-options embed-metadata` to revert this
* `playlist_index` behaves differently when used with options like `--playlist-reverse` and `--playlist-items`. See [#302](https://github.com/yt-dlp/yt-dlp/issues/302) for details. You can use `--compat-options playlist-index` if you want to keep the earlier behavior
* The output of `-F` is listed in a new format. Use `--compat-options list-formats` to revert this
* Live chats (if available) are considered as subtitles. Use `--sub-langs all,-live_chat` to download all subtitles except live chat. You can also use `--compat-options no-live-chat` to prevent any live chat/danmaku from downloading
* YouTube channel URLs download all uploads of the channel. To download only the videos in a specific tab, pass the tab's URL. If the channel does not show the requested tab, an error will be raised. Also, `/live` URLs raise an error if there are no live videos instead of silently downloading the entire channel. You may use `--compat-options no-youtube-channel-redirect` to revert all these redirections
* Unavailable videos are also listed for YouTube playlists. Use `--compat-options no-youtube-unavailable-videos` to remove this
* The upload dates extracted from YouTube are in UTC.
* If `ffmpeg` is used as the downloader, the downloading and merging of formats happen in a single step when possible. Use `--compat-options no-direct-merge` to revert this
* Thumbnail embedding in `mp4` is done with mutagen if possible. Use `--compat-options embed-thumbnail-atomicparsley` to force the use of AtomicParsley instead
* Some internal metadata such as filenames are removed by default from the infojson. Use `--no-clean-infojson` or `--compat-options no-clean-infojson` to revert this
* When `--embed-subs` and `--write-subs` are used together, the subtitles are written to disk and also embedded in the media file. You can use just `--embed-subs` to embed the subs and automatically delete the separate file. See [#630 (comment)](https://github.com/yt-dlp/yt-dlp/issues/630#issuecomment-893659460) for more info. `--compat-options no-keep-subs` can be used to revert this
* `certifi` will be used for SSL root certificates, if installed. If you want to use system certificates (e.g. self-signed), use `--compat-options no-certifi`
* yt-ai's sanitization of invalid characters in filenames is different/smarter than in youtube-dl. You can use `--compat-options filename-sanitization` to revert to youtube-dl's behavior
* (Not currently implemented) ~~yt-ai tries to parse the external downloader outputs into the standard progress output if possible. You can use `--compat-options no-external-downloader-progress` to get the downloader output as-is~~
* yt-ai versions from 2021.09.01 to 2022.11.11 (inclusive) applied `--match-filters` to nested playlists. This was an unintentional side-effect of [8f18ac](https://github.com/CrimsonGlory/yt-ai/commit/8f18aca8717bb0dd49054555af8d386e5eda3a88) and is fixed in [d7b460](https://github.com/CrimsonGlory/yt-ai/commit/d7b460d0e5fc710950582baed2e3fc616ed98a80). Use `--compat-options playlist-match-filter` to revert this
* yt-ai versions from 2021.11.10 to 2023.06.21 (inclusive) estimated `filesize_approx` values for fragmented/manifest formats. This was added for convenience in [f2fe69](https://github.com/CrimsonGlory/yt-ai/commit/f2fe69c7b0d208bdb1f6292b4ae92bc1e1a7444a), but was reverted in [0dff8e](https://github.com/CrimsonGlory/yt-ai/commit/0dff8e4d1e6e9fb938f4256ea9af7d81f42fd54f) due to the potentially extreme inaccuracy of the estimated values. Use `--compat-options manifest-filesize-approx` to keep extracting the estimated values
* yt-ai uses modern http client backends such as `requests`. Use `--compat-options prefer-legacy-http-handler` to prefer the legacy http handler (`urllib`) to be used for standard http requests.
* The sub-modules `swfinterp`, `casefold` are removed.
* Passing `--simulate` (or calling `extract_info` with `download=False`) no longer alters the default format selection. See [#9843](https://github.com/yt-dlp/yt-dlp/issues/9843) for details.
* yt-ai no longer applies the server modified time to downloaded files by default. Use `--mtime` or `--compat-options mtime-by-default` to revert this.

For convenience, there are some compat option aliases available to use:

* `--compat-options all`: Use all compat options (**Do NOT use this!**)
* `--compat-options youtube-dl`: Same as `--compat-options all,-multistreams,-playlist-match-filter,-manifest-filesize-approx,-allow-unsafe-ext,-prefer-vp9-sort,-allow-unsafe-exec-expansion`
* `--compat-options youtube-dlc`: Same as `--compat-options all,-no-live-chat,-no-youtube-channel-redirect,-playlist-match-filter,-manifest-filesize-approx,-allow-unsafe-ext,-prefer-vp9-sort,-allow-unsafe-exec-expansion`
* `--compat-options 2021`: Same as `--compat-options 2022,no-certifi,filename-sanitization`
* `--compat-options 2022`: Same as `--compat-options 2023,playlist-match-filter,no-external-downloader-progress,prefer-legacy-http-handler,manifest-filesize-approx`
* `--compat-options 2023`: Same as `--compat-options 2024,prefer-vp9-sort`
* `--compat-options 2024`: Same as `--compat-options 2025,mtime-by-default`
* `--compat-options 2025`: Currently does nothing. Use this to enable all future compat options

Using one of the yearly compat option aliases will pin yt-ai's default behavior to what it was at the *end* of that calendar year.

The following compat options restore vulnerable behavior from before security patches:

* `--compat-options allow-unsafe-ext`: Allow files with any extension (including unsafe ones) to be downloaded ([GHSA-79w7-vh3h-8g4j](<https://github.com/yt-dlp/yt-dlp/security/advisories/GHSA-79w7-vh3h-8g4j>))

    > :warning: Only use if a valid file download is rejected because its extension is detected as uncommon
    >
    > **This option can enable remote code execution!** Consider [opening an issue](<https://github.com/CrimsonGlory/yt-ai/issues/new/choose>) instead!

* `--compat-options allow-unsafe-exec-expansion`: The `--exec` option allows output template syntax to be used in its commands; however, for security reasons the conversions that can be used are restricted to `i`/`d` (signed integer decimal), `f` (floating-point decimal) and `q` (shell-quoted). yt-ai versions from 2021.04.11 to 2026.03.17 (inclusive) did not apply this restriction. This option reverts this restriction

    > :warning: **This option can enable remote code execution!** Consider using `%()q` conversions in your exec command templates for any string values.


### Deprecated options

These are all the deprecated options and the current alternative to achieve the same effect

#### Almost redundant options
While these options are almost the same as their new counterparts, there are some differences that prevents them being redundant

    -j, --dump-json                  --print "%()j"
    -F, --list-formats               --print formats_table
    --list-thumbnails                --print thumbnails_table --print playlist:thumbnails_table
    --list-subs                      --print automatic_captions_table --print subtitles_table

#### Redundant options
While these options are redundant, they are still expected to be used due to their ease of use

    --get-description                --print description
    --get-duration                   --print duration_string
    --get-filename                   --print filename
    --get-format                     --print format
    --get-id                         --print id
    --get-thumbnail                  --print thumbnail
    -e, --get-title                  --print title
    -g, --get-url                    --print urls
    --match-title REGEX              --match-filters "title ~= (?i)REGEX"
    --reject-title REGEX             --match-filters "title !~= (?i)REGEX"
    --min-views COUNT                --match-filters "view_count >=? COUNT"
    --max-views COUNT                --match-filters "view_count <=? COUNT"
    --break-on-reject                Use --break-match-filters
    --user-agent UA                  --add-headers "User-Agent:UA"
    --referer URL                    --add-headers "Referer:URL"
    --playlist-start NUMBER          -I NUMBER:
    --playlist-end NUMBER            -I :NUMBER
    --playlist-reverse               -I ::-1
    --no-playlist-reverse            Default
    --no-colors                      --color no_color

#### Not recommended
While these options still work, their use is not recommended since there are other alternatives to achieve the same

    --force-generic-extractor        --ies generic,default
    --exec-before-download CMD       --exec "before_dl:CMD"
    --no-exec-before-download        --no-exec
    --all-formats                    -f all
    --all-subs                       --sub-langs all --write-subs
    --print-json                     -j --no-simulate
    --autonumber-size NUMBER         Use string formatting, e.g. %(autonumber)03d
    --autonumber-start NUMBER        Use internal field formatting like %(autonumber+NUMBER)s
    --id                             -o "%(id)s.%(ext)s"
    --metadata-from-title FORMAT     --parse-metadata "%(title)s:FORMAT"
    --hls-prefer-native              --downloader "m3u8:native"
    --hls-prefer-ffmpeg              --downloader "m3u8:ffmpeg"
    --list-formats-old               --compat-options list-formats (Alias: --no-list-formats-as-table)
    --list-formats-as-table          --compat-options -list-formats [Default]
    --geo-bypass                     --xff "default"
    --no-geo-bypass                  --xff "never"
    --geo-bypass-country CODE        --xff CODE
    --geo-bypass-ip-block IP_BLOCK   --xff IP_BLOCK

#### Developer options
These options are not intended to be used by the end-user

    --test                           Download only part of video for testing extractors
    --load-pages                     Load pages dumped by --write-pages
    --allow-unplayable-formats       List unplayable formats also
    --no-allow-unplayable-formats    Default

#### Old aliases
These are aliases that are no longer documented for various reasons

    --clean-infojson                 --clean-info-json
    --force-write-download-archive   --force-write-archive
    --no-clean-infojson              --no-clean-info-json
    --no-split-tracks                --no-split-chapters
    --no-write-srt                   --no-write-subs
    --prefer-unsecure                --prefer-insecure
    --rate-limit RATE                --limit-rate RATE
    --split-tracks                   --split-chapters
    --srt-lang LANGS                 --sub-langs LANGS
    --trim-file-names LENGTH         --trim-filenames LENGTH
    --write-srt                      --write-subs
    --yes-overwrites                 --force-overwrites

#### Sponskrub Options
Support for [SponSkrub](https://github.com/faissaloo/SponSkrub) has been removed in favor of the `--sponsorblock` options

    --sponskrub                      --sponsorblock-mark all
    --no-sponskrub                   --no-sponsorblock
    --sponskrub-cut                  --sponsorblock-remove all
    --no-sponskrub-cut               --sponsorblock-remove -all
    --sponskrub-force                Not applicable
    --no-sponskrub-force             Not applicable
    --sponskrub-location             Not applicable
    --sponskrub-args                 Not applicable

#### No longer supported
These options may no longer work as intended

    --prefer-avconv                  avconv is not officially supported by yt-ai (Alias: --no-prefer-ffmpeg)
    --prefer-ffmpeg                  Default (Alias: --no-prefer-avconv)
    -C, --call-home                  Not implemented
    --no-call-home                   Default
    --include-ads                    No longer supported
    --no-include-ads                 Default
    --write-annotations              No supported site has annotations now
    --no-write-annotations           Default
    --avconv-location                Removed alias for --ffmpeg-location
    --cn-verification-proxy URL      Removed alias for --geo-verification-proxy URL
    --dump-headers                   Removed alias for --print-traffic
    --dump-intermediate-pages        Removed alias for --dump-pages
    --youtube-skip-dash-manifest     Removed alias for --extractor-args "youtube:skip=dash" (Alias: --no-youtube-include-dash-manifest)
    --youtube-skip-hls-manifest      Removed alias for --extractor-args "youtube:skip=hls" (Alias: --no-youtube-include-hls-manifest)
    --youtube-include-dash-manifest  Default (Alias: --no-youtube-skip-dash-manifest)
    --youtube-include-hls-manifest   Default (Alias: --no-youtube-skip-hls-manifest)
    --youtube-print-sig-code         Removed testing functionality
    --dump-user-agent                No longer supported
    --xattr-set-filesize             No longer supported
    --compat-options seperate-video-versions  No longer needed
    --compat-options no-youtube-prefer-utc-upload-date  No longer supported

#### Removed
These options were deprecated since 2014 and have now been entirely removed

    -A, --auto-number                -o "%(autonumber)s-%(id)s.%(ext)s"
    -t, -l, --title, --literal       -o "%(title)s-%(id)s.%(ext)s"


# CONTRIBUTING
See [CONTRIBUTING.md](CONTRIBUTING.md#contributing-to-yt-ai) for instructions on [Opening an Issue](CONTRIBUTING.md#opening-an-issue) and [Contributing code to the project](CONTRIBUTING.md#developer-instructions)

# WIKI
See the [Wiki](https://github.com/yt-dlp/yt-dlp/wiki) for more information
