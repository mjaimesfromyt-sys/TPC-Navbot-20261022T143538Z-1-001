# Model customization decision: base model with grounded retrieval

## Decision and actual work

No LoRA, QLoRA, or full fine-tuning experiment was performed for this project. There are no adapter weights, training logs, GPU utilization measurements, or model-quality gains to report. The course guide (p7) permits a well-reasoned decision to use the base/instruction-tuned model as-is.

The present priority is reviewed campus evidence and reliable multilingual scope/fallback behavior. Training on generated room numbers would encourage the model to reproduce unverified facts. A fine-tuned model would still need retrieval, current source approvals, missing-data behavior, and explicit route validation. Campus information can change without a new training run; the reviewed source registry handles those updates directly.

Optional Gemini integration uses a hosted base model through its API. This application does not control or fine-tune those hosted weights. Retained embedding experiments include an actual local open-source MiniLM encoder and a separately labelled lexical fallback. An encoder experiment does not demonstrate training a generative foundation model. Lexical hashing is not a foundation model or a fine-tuning experiment.

## PEFT and memory reasoning

LoRA freezes base weights and learns low-rank update matrices. For a projection with dimensions `d_out x d_in`, rank `r` introduces `r*(d_in+d_out)` trainable parameters instead of training `d_in*d_out` base parameters. For a hypothetical `4096 x 4096` projection at rank 8, this is 65,536 adapter parameters versus 16,777,216 base parameters, about 0.39%. This arithmetic is illustrative; it is not a measured project configuration. [Original LoRA paper](https://arxiv.org/abs/2106.09685).

QLoRA trains low-rank adapters through a frozen quantized base model, using 4-bit quantization and techniques including double quantization and paged optimizers. Quantizing a hypothetical 7-billion-parameter model to exactly four bits implies a 3.5 GB raw weight payload before quantization metadata, adapters, optimizer state, activations, temporary buffers, and runtime overhead. This is a lower-bound payload calculation, not a guarantee that training fits on a particular GPU. [Original QLoRA paper](https://arxiv.org/abs/2305.14314).

No local GPU capacity or training budget was supplied or verified. The cited papers demonstrate mechanisms and their own experiments, not performance of this project. A memory plan must include sequence length, batch size, optimizer state, attention implementation, and activation checkpointing before selecting hardware.

## What a future experiment should test

A useful future target would be intent classification or consistent concise Bisaya/Tagalog fallback phrasing, rather than memorizing campus locations. First collect authorized, de-identified student questions and independently reviewed labels. Split by paraphrase families and destinations to reduce leakage. Include unrelated requests containing campus words, unsupported campus information, mixed requests, ambiguous rooms, and adversarial overrides.

Compare the unchanged base model, prompted base model, and adapter under the same held-out set. Report scope precision/recall per language, unsupported-fact rate, correct clarification rate, and latency/memory measurements. Preserve all failures and the exact model/adapters/configuration. The deterministic route and source checks must remain active regardless of training results.

Training is justified only if a measured deficiency survives better data, prompting, and clear application rules. Until then, reviewed retrieval and a narrow validated model role are easier to audit and update. This is a reasoned decision, not a claim that fine-tuning can never help.
