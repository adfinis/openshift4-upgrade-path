# openshift4-upgrade-path

This script computes a shortest upgrade path between two OpenShift
versions, using the same API the OpenShift cluster itself uses to get
the list of available upgrades.

## Usage

Just pass the current and target version as command line arguments:

```sh
$ ./openshift4-upgrade-path.py 4.1.15 4.3.18
Shortest Upgrade path from 4.1.15 to 4.3.18:
  4.1.15 -> 4.1.24 using stable-4.1
  4.1.24 -> 4.1.38 using stable-4.2
  4.1.38 -> 4.2.27 using stable-4.2
  4.2.27 -> 4.3.18 using stable-4.3
```

If there is no upgrade path available:

```sh
$ ./openshift4-upgrade-path.py 4.1.41 4.3.18
No upgrade path from 4.1.41 to 4.3.18 found, using channels stable-4.1, stable-4.2, stable-4.3
```

### Options

The `fast-4.*` and `candidate-4.*` upgrade channels can be enabled
using the `--fast` and `--candidate` flags, respectively:

```sh
$ ./openshift4-upgrade-path.py --fast --candidate 4.1.41 4.3.18
Shortest Upgrade path from 4.1.41 to 4.3.18:
  4.1.41 -> 4.2.30 using candidate-4.2
  4.2.30 -> 4.3.18 using candidate-4.3
```

Be advised that using the `candidate-4.*` channels may result in
unsupported upgrade paths and should not be used for production-grade
clusters.

If your cluster is running on a supported architecture other than
`x86_64`, you can specify the architecture using the `--arch` flag:

```sh
$ ./openshift4-upgrade-path.py --candidate --arch s390x 4.2.30 4.3.18
Shortest Upgrade path from 4.2.30 to 4.3.18:
  4.2.30 -> 4.3.18 using candidate-4.3
```
