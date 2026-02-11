SHELL := /bin/bash

PYTHON ?= python3
VENV ?= .venv
RUN := $(VENV)/bin/python
PIP := $(RUN) -m pip

CREDENTIALS_FILE ?= $(HOME)/.config/gcp/tts-oauth-user.json
CLIENT_SECRET ?=
PROJECT_ID ?=

TEXT ?=
OUT ?= ./out/tts.mp3
VOICE ?= en-US-Chirp3-HD-Fenrir
LANGUAGE ?= en-US
MODEL ?=
FORMAT ?= mp3
SPEAKING_RATE ?= 1.0
PITCH ?= 0.0
USAGE_LOG ?= usage_log.csv
VOICES_LANGUAGE ?=
VOICE_FAMILY ?= Chirp3
TEST_TEXT_FILE ?= ./test_sentence.txt
TEST_OUT ?= ./out/test-sentence.mp3
OUT_DIR ?= ./out
VOICE_FAMILIES ?= Chirp3,Neural2
LIMIT ?= 0
MCP_PROFILES ?= ./tts_profiles.json
MCP_PROFILE ?=

.PHONY: help setup oauth-login speak speak-ssml speak-test speak-us-all voices doctor mcp-setup mcp-run mcp-doctor

help:
	@echo "Targets:"
	@echo "  make setup"
	@echo "  make oauth-login CLIENT_SECRET=~/Downloads/<oauth-client>.json [PROJECT_ID=<gcp-project-id>]"
	@echo "  make speak TEXT=\"Hello from speech\" [MODEL=models/chirp3-hd] [OUT=./out/hello.mp3]"
	@echo "  make speak-ssml TEXT=\"<speak>Hello <break time='500ms'/> world</speak>\""
	@echo "  make speak-test [VOICE=en-US-Chirp3-HD-Fenrir] [OUT=./out/test-sentence.mp3]"
	@echo "  make speak-us-all [OUT_DIR=./out] [VOICE_FAMILIES=Chirp3,Neural2] [LIMIT=0]"
	@echo "  make voices [VOICES_LANGUAGE=en-US] [VOICE_FAMILY=Chirp3]"
	@echo "  make doctor"
	@echo "  make mcp-setup"
	@echo "  make mcp-run [MCP_PROFILES=./tts_profiles.json] [MCP_PROFILE=opencode]"
	@echo "  make mcp-doctor [MCP_PROFILES=./tts_profiles.json] [MCP_PROFILE=opencode]"

setup:
	@test -d "$(VENV)" || $(PYTHON) -m venv "$(VENV)"
	@$(PIP) install --quiet -r requirements.txt

oauth-login: setup
	@if [[ -z "$(CLIENT_SECRET)" ]]; then \
		echo "Missing CLIENT_SECRET."; \
		echo "Example: make oauth-login CLIENT_SECRET=~/Downloads/client_secret_abc.json PROJECT_ID=my-project"; \
		exit 1; \
	fi
	@if [[ -n "$(PROJECT_ID)" ]]; then \
		$(RUN) oauth_login.py \
			--client-secret-file "$(CLIENT_SECRET)" \
			--out "$(CREDENTIALS_FILE)" \
			--quota-project "$(PROJECT_ID)"; \
	else \
		$(RUN) oauth_login.py \
			--client-secret-file "$(CLIENT_SECRET)" \
			--out "$(CREDENTIALS_FILE)"; \
	fi

speak: setup
	@if [[ -z "$(TEXT)" ]]; then \
		echo "Missing TEXT."; \
		echo "Example: make speak TEXT=\"Hello from speech\""; \
		exit 1; \
	fi
	@GOOGLE_APPLICATION_CREDENTIALS="$(CREDENTIALS_FILE)" \
		$(RUN) speak.py \
			--text "$(TEXT)" \
			--voice "$(VOICE)" \
			--language "$(LANGUAGE)" \
			$(if $(MODEL),--model "$(MODEL)") \
			--format "$(FORMAT)" \
			--speaking-rate "$(SPEAKING_RATE)" \
			--pitch "$(PITCH)" \
			--usage-log "$(USAGE_LOG)" \
			--out "$(OUT)"

speak-ssml: setup
	@if [[ -z "$(TEXT)" ]]; then \
		echo "Missing TEXT (SSML)."; \
		echo "Example: make speak-ssml TEXT=\"<speak>Hello <break time='500ms'/> world</speak>\""; \
		exit 1; \
	fi
	@GOOGLE_APPLICATION_CREDENTIALS="$(CREDENTIALS_FILE)" \
		$(RUN) speak.py \
			--ssml \
			--text "$(TEXT)" \
			--voice "$(VOICE)" \
			--language "$(LANGUAGE)" \
			$(if $(MODEL),--model "$(MODEL)") \
			--format "$(FORMAT)" \
			--speaking-rate "$(SPEAKING_RATE)" \
			--pitch "$(PITCH)" \
			--usage-log "$(USAGE_LOG)" \
			--out "$(OUT)"

speak-test:
	@GOOGLE_APPLICATION_CREDENTIALS="$(CREDENTIALS_FILE)" \
		$(RUN) speak.py \
			--text-file "$(TEST_TEXT_FILE)" \
			--voice "$(VOICE)" \
			--language "$(LANGUAGE)" \
			$(if $(MODEL),--model "$(MODEL)") \
			--format "$(FORMAT)" \
			--speaking-rate "$(SPEAKING_RATE)" \
			--pitch "$(PITCH)" \
			--usage-log "$(USAGE_LOG)" \
			--out "$(TEST_OUT)"

speak-us-all: setup
	@GOOGLE_APPLICATION_CREDENTIALS="$(CREDENTIALS_FILE)" \
		$(RUN) batch_generate_us.py \
			--text-file "$(TEST_TEXT_FILE)" \
			--out-dir "$(OUT_DIR)" \
			--families "$(VOICE_FAMILIES)" \
			--language "en-US" \
			--format "$(FORMAT)" \
			--speaking-rate "$(SPEAKING_RATE)" \
			--pitch "$(PITCH)" \
			--limit "$(LIMIT)"

voices: setup
	@GOOGLE_APPLICATION_CREDENTIALS="$(CREDENTIALS_FILE)" \
		$(RUN) list_voices.py \
			--language "$(VOICES_LANGUAGE)" \
			--family "$(VOICE_FAMILY)"

doctor: setup
	@if [[ -f "$(CREDENTIALS_FILE)" ]]; then \
		echo "Credentials file found: $(CREDENTIALS_FILE)"; \
	else \
		echo "Credentials file not found: $(CREDENTIALS_FILE)"; \
		echo "Run: make oauth-login CLIENT_SECRET=~/Downloads/<oauth-client>.json PROJECT_ID=<gcp-project-id>"; \
	fi
	@echo "Voice default: $(VOICE)"
	@echo "Model default: $(if $(MODEL),$(MODEL),<provider default>)"
	@echo "Output default: $(OUT)"

mcp-setup: setup

mcp-run: mcp-setup
	@GOOGLE_APPLICATION_CREDENTIALS="$(CREDENTIALS_FILE)" \
		$(RUN) mcp_server.py \
			--profiles "$(MCP_PROFILES)" \
			$(if $(MCP_PROFILE),--profile "$(MCP_PROFILE)")

mcp-doctor: mcp-setup
	@GOOGLE_APPLICATION_CREDENTIALS="$(CREDENTIALS_FILE)" \
		$(RUN) mcp_server.py \
			--profiles "$(MCP_PROFILES)" \
			$(if $(MCP_PROFILE),--profile "$(MCP_PROFILE)") \
			--doctor
