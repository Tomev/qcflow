# Introduction

This file contains information I found useful
during `qcflow` development. As stated in the
`README.md`, `qcflow` is `mlflow` repurposed for
quantum experiments tracking and cataloguing. 
This file is also repurposed version of the
[mlflow CONTRIBUTING.md](https://github.com/mlflow/mlflow/blob/master/CONTRIBUTING.md).

## Development notes

- Running standard `qcflow ui` requires one to 
build required files. See the UI section of this
doc, especially [Building a Distributable Artifact
section](#building-a-distributable-artifact).

## UI

### JavaScript and UI

The QCFlow UI is written in JavaScript. `yarn` is required to run the
Javascript dev server and the tracking UI. You can verify that `yarn` is
on the PATH by running `yarn -v`, and [install
yarn](https://classic.yarnpkg.com/lang/en/docs/install) if needed.

#### Install Node Module Dependencies

On OSX, install the following packages required by the node modules:

```bash
brew install pixman cairo pango jpeg
```

Linux/Windows users will need to source these dependencies using the
appropriate package manager on their platforms.

#### Install Node Modules

Before running the Javascript dev server or building a distributable
wheel, install Javascript dependencies via:

```bash
cd qcflow/server/js
yarn install
cd - # return to root repository directory
```

If modifying dependencies in `qcflow/server/js/package.json`, run `yarn upgrade` within `qcflow/server/js` to install the updated dependencies.

#### Launching the Development UI

We recommend [Running the Javascript Dev
Server](#running-the-javascript-dev-server) - otherwise, the tracking
frontend will request files in the `qcflow/server/js/build` directory,
which is not checked into Git. Alternatively, you can generate the
necessary files in `qcflow/server/js/build` as described in [Building a
Distributable Artifact](#building-a-distributable-artifact).

#### Running the Javascript Dev Server

[Install Node Modules](#install-node-modules), then run the following:

In one shell:

```bash
qcflow ui
```

In another shell:

```bash
cd qcflow/server/js
yarn start
```

The Javascript Dev Server will run at <http://localhost:3000> and the
QCFlow server will run at <http://localhost:5000> and show runs logged
in `./qcruns`.

#### Building a Distributable Artifact

If you would like to build a fully functional version of QCFlow from your local branch for testing or a local patch fix, first
[install the Node Modules](#install-node-modules), then run the following:

Generate JS files in `qcflow/server/js/build`:

```bash
cd qcflow/server/js
yarn build
```

Build a pip-installable wheel and a compressed code archive in `dist/`:

```bash
cd -
python -m build
```