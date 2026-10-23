# Containerization, configuration, and deployment evidence

## Streamlit Community Cloud

Deployment is prepared locally; no remote deployment is claimed.

1. Commit and push the reviewed application changes, school-confirmed raw records,
   `data/source_registry.json`, assets, dependencies, and root `.streamlit/config.toml`.
2. In Streamlit Community Cloud, create an app from repository
   `mjaimesfromyt-sys/TPC-Navbot-20261022T143538Z-1-001` and the branch containing
   the final changes. Set the main file path to **`TPC Navbot/app.py`**.
3. In Advanced settings select Python **3.13**, the version tested locally.
   For the offline configuration used in the local chat checks, add these
   root-level values in Secrets:

   ```toml
   TPC_EMBEDDING_MODE = "lexical"
   TPC_ENABLE_LLM_SELECTION = "0"
   ```

   This mode needs no API key or downloaded model. It uses lexical retrieval
   with campus aliases and approved structured facts. It is not semantic
   embedding retrieval. A separately provisioned local model can enable semantic
   mode later.
4. Deploy, inspect build/startup logs, and test `crim building`, `registrar`,
   `Asa ang library?`, `How do I enroll?`, a suggested follow-up, an unknown
   phone number, and an unrelated question. Retain the URL and commit used.

Community Cloud runs from the repository root. The root configuration is included
for this reason; `TPC Navbot/requirements.txt` sits beside the entrypoint and
declares the dependencies. Application paths resolve from the project directory.
The source registry and raw files are durable inputs in Git; runtime indexes
are rebuilt from them and are not an editing interface for school records.

See the official [file organization guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization),
[deployment guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy),
and [secrets setup](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management).

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
