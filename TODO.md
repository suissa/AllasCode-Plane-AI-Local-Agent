# TODO: WhatsApp Gateway Migration to Evolution Go

This checklist breaks the requested WhatsApp gateway migration into reviewable implementation tasks. The goal is to replace the agent's default WhatsApp gateway behavior with the project located at `Planes/Agents/AIHermesAgent/gateway/platforms/whatsapp`, while changing as little of the existing Hermes Agent code as possible.

## 1. Discovery and Baseline Mapping

- [ ] Inspect the existing Hermes gateway startup flow and identify the current default gateway/platform selection points.
- [ ] Inspect the existing WhatsApp platform implementation under `gateway/platforms/whatsapp`.
- [ ] Inspect or import the external project at `Planes/Agents/AIHermesAgent/gateway/platforms/whatsapp` and document its expected commands, environment variables, API routes, and runtime requirements.
- [ ] Identify the minimum Hermes files that must change to redirect WhatsApp actions to the new local API service.
- [ ] Confirm how Hermes configuration currently stores gateway platform credentials, especially the WhatsApp gateway `su` setting mentioned in the request.

## 2. Evolution Go Documentation Route Scraper

- [ ] Create a pure JavaScript scraper with no external dependencies, using only `fetch` and regular expressions.
- [ ] Start scraping from `https://docs.evolutionfoundation.com.br/evolution-go/get-all-instances`.
- [ ] Parse `div#pagination` from each route page and extract the next route URL from the pagination link.
- [ ] Continue crawling route pages until no next route is found or a loop is detected.
- [ ] Persist discovered routes to `Planes/Agents/AIHermesAgent/gateway/platforms/whatsapp/routes.json`.
- [ ] Store enough route metadata in `routes.json` for the agent to decide which local API route to call.
- [ ] Add deterministic behavior so rerunning the scraper updates `routes.json` without duplicating entries.
- [ ] Document how to rerun the scraper.

## 3. Local WhatsApp API Service Installation and Environment

- [ ] Review the Evolution Go installation documentation at `https://docs.evolutionfoundation.com.br/evolution-go/installation`.
- [ ] Define the expected `.env` file for the local WhatsApp service.
- [ ] Ensure any generated or modified `.env` changes `SERVER_PORT=8008` to `SERVER_PORT=9991`.
- [ ] Add validation that the service configuration points to port `9991`.
- [ ] When Hermes is configured to use this gateway locally, run `make build` before the first `make dev`.
- [ ] When the agent starts and WhatsApp gateway `su` is configured, start the local service with `make dev`.
- [ ] Before starting or using Hermes after installation, verify the local WhatsApp API is reachable.
- [ ] Decide how Hermes should report a clear startup error if the local WhatsApp API is not reachable.

## 4. Docker Installation Path

- [ ] Detect or read whether the developer configured Hermes to run this gateway via Docker.
- [ ] Implement the Docker installation path according to the Evolution Go installation documentation.
- [ ] Ensure the Docker path still applies `SERVER_PORT=9991` in the generated environment.
- [ ] Verify Docker startup performs the same API health check as the local `make dev` path.
- [ ] Document any Docker-specific prerequisites or failure modes.

## 5. Hermes Gateway Integration

- [ ] Replace each existing WhatsApp gateway operation with a call to the new local API service.
- [ ] Keep existing Hermes gateway interfaces stable wherever possible.
- [ ] Avoid broad rewrites of `gateway/run.py`, `cli.py`, or unrelated platform adapters.
- [ ] Add a small adapter/client layer if needed so message send operations call the local API consistently.
- [ ] Ensure the agent only needs to send the desired message via API, rather than managing low-level WhatsApp behavior itself.
- [ ] Make the route lookup consult `routes.json` so the agent can understand which local API route should execute.
- [ ] Preserve existing logging, error handling, and gateway session behavior as much as possible.

## 6. TUI and Configuration Flow

- [ ] Validate the current TUI installation/configuration flow for gateway setup.
- [ ] If non-interactive automation cannot drive the TUI, create the final expected configuration file directly.
- [ ] Add or document a command in the form `hermes config "{path to config file}"` to generate an already-configured agent without completing the TUI prompts.
- [ ] Ensure the generated config selects the new WhatsApp gateway implementation.
- [ ] Ensure the generated config includes any needed service path, port, startup mode, and credentials.

## 7. Build and Runtime Validation

- [ ] Run `make build` for the WhatsApp service and record the result.
- [ ] Start the WhatsApp service with `make dev` or the Docker equivalent.
- [ ] Verify the local API is listening on port `9991`.
- [ ] Launch Hermes with the generated/configured WhatsApp gateway settings.
- [ ] Confirm Hermes detects the configured WhatsApp gateway and checks the API health before use.
- [ ] Send a test message through the Hermes gateway path and confirm the local API receives it.
- [ ] Add targeted tests or smoke checks around the new adapter/client behavior.
- [ ] Run the appropriate Hermes test wrapper for touched code paths.

## 8. Documentation

- [ ] Create `WHATSAPP-IMPLEMENTATION.md`.
- [ ] Explain every existing Hermes code path modified for the gateway migration.
- [ ] For each changed behavior, document how it worked before and how it works now.
- [ ] Document local setup, Docker setup, generated `.env`, required port `9991`, `make build`, `make dev`, health checks, and troubleshooting.
- [ ] Document how `routes.json` is generated and how Hermes uses it.
- [ ] Include the exact validation commands used during implementation.

## 9. Final Review

- [ ] Confirm the implementation changes the minimum possible amount of existing Hermes Agent code.
- [ ] Confirm all generated files are committed intentionally and no secrets are committed.
- [ ] Confirm docs and code agree on port `9991`.
- [ ] Confirm the scraper uses no external JavaScript libraries.
- [ ] Confirm the final commit includes the implementation, scraper, generated route map, docs, and tests.
