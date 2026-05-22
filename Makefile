# Makefile shim — delegates all targets to justfile.
# Use: make <target>  →  just <target>
# Run `just --list` to see available recipes.

JUST := $(shell which just 2>/dev/null)

.PHONY: %
%:
	@$(JUST) $@
