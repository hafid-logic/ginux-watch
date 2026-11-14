# Gate-style repro for the C-2 property tests. Run from the repo root:
#   make -f property-tests/Makefile test
# Overrides: UPSTREAM_CHECKOUT=<path> CARGO=<cargo-binary>
UPSTREAM_CHECKOUT ?= /home/z/my-project/work/upstream-ginux
CARGO ?= cargo

.PHONY: test
test:
	@test -e upstream || ln -sfn "$(UPSTREAM_CHECKOUT)" upstream
	$(CARGO) test --manifest-path property-tests/Cargo.toml

.PHONY: clean
clean:
	$(CARGO) clean --manifest-path property-tests/Cargo.toml
