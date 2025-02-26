# Djerba Demonstration

![Djerba](./doc/djerba_logo_small.png)

Demonstration of a modular system to create reports from metadata and workflow output

## Introduction

Djerba has been developed at the [Ontario Institute for Cancer Research](https://oicr.on.ca/) (OICR) to generate clinical reports for cancer research.

This is a fork of Djerba intended for demonstration. See the [main Djerba repository](https://github.com/oicr-gsi/djerba) and [documentation on ReadTheDocs](https://djerba.readthedocs.io/en/latest/) for information on how Djerba is used in production.

This demo accompanies a presentation given at [ISMB 2024](https://www.iscb.org/ismb2024/home) on 2024-07-15: [Djerba: Sharing and Updating a Modular System for Clinical Report Generation](./doc/Iain_Bancarz_presentation_ISMB_2024_Djerba.pdf)

## Installation and FAQs

For detailed instructions on how to install, test and run `djerba-demo`, see [HOWTO.md](./HOWTO.md).

We also have a [Frequently Asked Questions](./FAQ.md) file.

## Code Structure

Djerba has a modular structure based on _plugins_. The `djerba-demo` repo has a reduced set of plugins, and accordingly fewer dependencies. The core Djerba code, which loads and runs plugins, is the same as the version deployed in production at OICR, in order for `djerba-demo` to provide an accurate demonstration of how Djerba and its plugins work.

For development history, see the [changelog](./CHANGELOG.md).

## Copyright and License

Copyright &copy; 2024 by Genome Sequence Informatics, Ontario Institute for Cancer Research.

Licensed under the [GPL 3.0 license](https://www.gnu.org/licenses/gpl-3.0.en.html).
