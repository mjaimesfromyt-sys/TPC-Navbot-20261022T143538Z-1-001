# Containerization, configuration, and deployment evidence

## Local container workflow

From the `TPC Navbot` project directory:

```powershell
docker build -t tpc-navbot:local .
docker run --rm -p 8501:8501 --env-file .env tpc-navbot:local
```

Or use `docker compose up --build`. Open `http://localhost:8501` and test a campus request, an unrelated request, and a localized fallback. Use only authorized reviewed data for actual campus answers. All bundled samples remain unverified.

The Dockerfile separates dependency construction from the runtime stage and runs the application as a non-root user. Healthchecks must use tooling available in the final image; a successful build alone does not establish application health. Retain the build output, container health state, and a screenshot or recording from the actual environment.

The current source supports local semantic embeddings only when the chosen model is already cached. A fresh container can report lexical fallback unless the operator deliberately provisions model files. Report the real backend; do not assume installing a package downloaded a model.

## Environment and secrets

Copy `.env.example` to a private `.env` for development. `GEMINI_API_KEY` belongs in an environment variable or the hosting platform's secret store. Never commit credentials, place them in documentation screenshots, bake `.env` into an image, or print provider exceptions containing secrets. The deterministic offline mode does not require a key.

`TPC_ENABLE_LLM_SELECTION=1` opts into constrained provider-backed source selection. Keep it off until the deployment is authorized to send the candidate information to the provider. `TPC_EMBEDDING_MODE` is `auto`, `semantic`, or `lexical`. Relative data/index/registry overrides resolve from the project root; see `.env.example` and `src/config.py`.

Persist the review registry, raw documents, and vector-store snapshot according to the deployment's configuration. Back up approved source evidence and reviews together. Review changes and raw-file changes must trigger an ingestion refresh. Legacy unverified Chroma collections are not accepted as approved evidence.

## CI and deployment distinction

GitHub only discovers workflows under the repository-root `.github/workflows/`. The original nested workflow path was insufficient. The root pipeline should run offline regressions and demonstration checks before a container build. A green pipeline is evidence only after it actually runs for the submitted commit; a YAML file is configuration, not a successful run.

Do not place an API key in public test fixtures. A later authorized API integration job can use a protected secret and approved test content; retain a redacted success/failure artifact. A local stub validates handling logic but is not proof of a successful external API call.

## Evidence still required for checkpoint 4

The course guide (p7) requires the containerized app to run **outside the local machine**, with a screenshot, public/sandbox URL, or recorded run. No external deployment is claimed here. The student must choose an authorized host and retain:

1. Exact Git commit, image tag/digest, build log, and deployed runtime configuration without secrets.
2. Reachable URL or recording that identifies the remote environment and container health.
3. Five representative interactions, including an unrelated refusal and unavailable campus information.
4. Actual embedding/storage/framework backends and whether optional model selection is enabled.
5. Source-registry review status and a record of any approved campus data included.

These are an evidence checklist, not invented deployment results. Use the requirements audit to record which actual artifacts are still missing.
