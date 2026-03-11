# ESPHome Development Makefile
# Usage: make <target>  (default config: esp32s3box3.yaml)

CONFIG    ?= esp32s3box3.yaml
PORT      ?= /dev/cu.usbserial-*
ESPHOME   := esphome

.PHONY: help compile flash logs validate clean dashboard upload \
        secrets-check yaml-check check diff ralph ralph-init \
        push tags status feature fix pr merge pins

# ──────────────────────────────────────────────
#  Default: show help
# ──────────────────────────────────────────────
help:
	@echo ""
	@echo "  ESPHome Dev — $(CONFIG)"
	@echo ""
	@echo "  ── Firmware ──────────────────────────────────────────────"
	@echo "  make compile          Compile firmware (no flash)"
	@echo "  make flash            Compile + flash via USB-C"
	@echo "  make ota              Compile + flash via OTA (Wi-Fi)"
	@echo "  make logs             Stream device logs"
	@echo "  make validate         YAML schema validation only"
	@echo "  make yaml-check       Python YAML syntax check (fast, no ESPHome)"
	@echo "  make secrets-check    Confirm secrets.yaml has real values (not placeholders)"
	@echo "  make pins             GPIO conflict + strapping pin validation (run before flash!)"
	@echo "  make check            Run all pre-flight checks (yaml + pins + validate)"
	@echo "  make clean            Remove build cache (.esphome/)"
	@echo "  make dashboard        Open ESPHome web dashboard"
	@echo ""
	@echo "  ── Git / PR workflow ────────────────────────────────────"
	@echo "  make feature NAME=x   Create + checkout new feat/x branch"
	@echo "  make fix NAME=x       Create + checkout new fix/x branch"
	@echo "  make pr               Push current branch + open draft PR"
	@echo "  make merge            Auto-merge PR for current branch (squash)"
	@echo "  make diff             Show staged git changes"
	@echo "  make status           Show branch / remote / tag info"
	@echo "  make tags             List last 10 version tags"
	@echo ""
	@echo "  CONFIG=$(CONFIG)  (override: make flash CONFIG=other.yaml)"
	@echo ""

# ──────────────────────────────────────────────
#  Core ESPHome commands
# ──────────────────────────────────────────────
compile:
	$(ESPHOME) compile $(CONFIG)

flash: pins
	$(ESPHOME) run $(CONFIG)

ota: pins
	$(ESPHOME) run $(CONFIG) --no-logs

logs:
	$(ESPHOME) logs $(CONFIG)

validate:
	$(ESPHOME) config $(CONFIG)

clean:
	rm -rf .esphome/build .esphome/cache
	@echo "Build cache cleared."

dashboard:
	$(ESPHOME) dashboard .

# ──────────────────────────────────────────────
#  Pre-flight checks (fast, no compile needed)
# ──────────────────────────────────────────────
yaml-check:
	@echo "→ YAML syntax check..."
	@python3 -c "\
import yaml, sys; \
loader = yaml.SafeLoader; \
loader.add_multi_constructor('', lambda l,t,n: None); \
[yaml.load(open(f), loader) for f in sys.argv[1:]]; \
print('  ✓ All YAML files parse OK')" *.yaml \
		|| (echo "  ✗ YAML syntax error — run 'esphome config $(CONFIG)' for details" && exit 1)

secrets-check:
	@echo "→ Secrets placeholder check..."
	@if grep -q "YourWiFi\|YourPassword\|your_ssid\|PLACEHOLDER\|changeme" secrets.yaml 2>/dev/null; then \
		echo "  ✗ secrets.yaml still has placeholder values — fill them in before flashing!"; \
		exit 1; \
	else \
		echo "  ✓ secrets.yaml looks populated"; \
	fi
	@if grep -q "your_chakra_light\b" $(CONFIG) 2>/dev/null; then \
		echo "  ⚠ chakra_light_entity is still the placeholder — update substitutions in $(CONFIG)"; \
	fi

check: yaml-check secrets-check pins validate
	@echo ""
	@echo "✓ All pre-flight checks passed."

# ──────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────
diff:
	git --no-pager diff --staged

pins:
	@echo "→ GPIO pin conflict + strapping check..."
	@python3 tools/pin_check.py $(CONFIG)

# ──────────────────────────────────────────────
#  Ralph Loop (autonomous AI agent)
# ──────────────────────────────────────────────
ralph-init:
	@~/bin/ralph init

ralph:
	@[ -f ralph.sh ] || (echo "Run 'make ralph-init' first"; exit 1)
	@bash ralph.sh

# ──────────────────────────────────────────────
#  GitHub / versioning
# ──────────────────────────────────────────────
push:
	git push origin $(shell git rev-parse --abbrev-ref HEAD)

tags:
	@git tag --sort=-v:refname | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$$' | head -10

status:
	@echo "Branch : $$(git rev-parse --abbrev-ref HEAD)"
	@echo "Remote : $$(git remote get-url origin 2>/dev/null || echo 'none')"
	@echo "Ahead  : $$(git rev-list @{u}..HEAD --count 2>/dev/null || echo '?') commits"
	@echo "Latest tag: $$(git tag --sort=-v:refname | grep -E '^v' | head -1 || echo 'none')"

# ──────────────────────────────────────────────
#  PR / Branch workflow
# ──────────────────────────────────────────────
feature:
	@[ -n "$(NAME)" ] || (echo "Usage: make feature NAME=my-feature-slug"; exit 1)
	git checkout -b feat/$(NAME)
	@echo "✓ Created and switched to feat/$(NAME)"
	@echo "  Commit your changes, then: make pr"

fix:
	@[ -n "$(NAME)" ] || (echo "Usage: make fix NAME=my-fix-slug"; exit 1)
	git checkout -b fix/$(NAME)
	@echo "✓ Created and switched to fix/$(NAME)"
	@echo "  Commit your changes, then: make pr"

pr:
	@BRANCH=$$(git rev-parse --abbrev-ref HEAD); \
	[ "$$BRANCH" != "main" ] || (echo "✗ Already on main — create a feature branch first: make feature NAME=xxx"; exit 1)
	git push -u origin $$(git rev-parse --abbrev-ref HEAD)
	gh pr create --fill --draft
	@echo "✓ Draft PR created. Review CI, then: make merge"

merge:
	@BRANCH=$$(git rev-parse --abbrev-ref HEAD); \
	[ "$$BRANCH" != "main" ] || (echo "✗ Already on main — switch to your feature branch first"; exit 1)
	gh pr merge --squash --auto --delete-branch
	git checkout main
	git pull --tags
	@echo "✓ PR merged → main. Tags pulled from remote."
