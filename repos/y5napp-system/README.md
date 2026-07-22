# Yakoon System

*The base system tree for Yakoon.*

Root is the default workspace bundle. It provides the system commands
and services that make up a Yakoon runtime environment.

## Structure

```
src/
├── usr/
│   ├── bin/              — System commands (cd, ls, su, …)
│   └── sbin/
│       └── ident         — Identity & permission setup
├── var/
│   └── welcome/          — Landing node
└── home/                 — User home mount point
```

## How it works

Root is not a shell. It is a **node tree** rooted at `/`. Every
subdirectory with a `.yak/` folder becomes a node in the runtime.

Commands are defined as flows in `.yak/run/`. Services are initialized
in `.yak/setup/`. Ports connect nodes across the tree.

## Built on Yakoon

Root is implemented entirely as a Yakoon bundle. It demonstrates
that a complete interactive environment can be built from the same
primitives — nodes, flows, ports and projections — that power every
other Yakoon space.
