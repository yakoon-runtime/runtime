# Shell

*A navigable runtime built on Yakoon.*

Most command shells execute commands.

Shell lets you navigate a live runtime.

Commands, sessions, jobs, remote runtimes and tools are organized as a
single node tree. Like a filesystem, but for a live runtime.

Instead of remembering long command names, you move through the runtime.

```
/
├── system
├── jobs
├── session
├── net
└── labs
```

Every node exposes commands.

```
cd jobs
list

cd session
attach work

ls shell/session

cd net
connect office
```

The current location becomes context.

```
cd session

man list
man session/list
```

shows the documentation for the current space.

```
list
```

invokes the local command.

The same command name may exist in different spaces without conflict.

## The Model

```
Runtime
│
▼
Node Tree
│
├── system
├── jobs
├── session
├── net
└── labs
```

Navigation is part of the interaction model, not just a convenience.
Users discover capabilities by navigating instead of remembering command names.

## What Shell is not

- Not a Unix shell.
- Not a terminal emulator.
- Not a scripting language.
- Not a REPL.

Shell is an interface to the Yakoon runtime.

It exposes runtime services through a navigable node tree and executes
every command as a Yakoon flow.

## The Name

A shell is normally an outer layer around an operating system.

Yakoon Shell takes that literally.

It is the outer layer of the runtime — the surface through which you
explore, inspect and control a live system.

## Built on Yakoon

Shell is implemented entirely as a Yakoon Space.

Every command is a flow.

Every result is a projection.

Every session is a runtime object.

The shell itself demonstrates that a complete interactive environment
can be built from the same primitives that power every other Yakoon
space.
