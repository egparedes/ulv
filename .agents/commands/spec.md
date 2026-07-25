---
description: Create a new feature spec directory under development/work/<YYYY-MM>-<slug>/
argument-hint: <kebab-case-slug>
---

You are creating a new feature spec.

1. If `$ARGUMENTS` is empty, ask the user for a slug before creating
   anything.
2. Compute today's date as `YYYY-MM`. The directory is
   `development/work/<YYYY-MM>-$ARGUMENTS/`.
3. Create the directory if it doesn't exist. **Do not** pre-create
   `plan.md`, `tasks.md`, `report.md`, or `scratch.md` — each role
   creates the deliverables it owns (Architect: `plan.md`/`tasks.md`;
   Developer: `report.md`), and pre-creating them would force those
   roles to `edit` files they should be able to `write` from scratch.
   `scratch.md` is not a deliverable but the feature's shared channel:
   whoever needs it first creates it, and everyone after that appends.
4. Delegate the actual spec authoring to the **product-owner** subagent
   (`.agents/subagents/product-owner.md`). It owns the spec format,
   the testable-criteria rule, the non-goals requirement, and the
   "stop and ask before planning" boundary.
5. If the product-owner hands back a **clarifying question** instead of
   `spec.md`, put it to the user, then re-invoke the product-owner
   subagent with the question and the user's answer included in the
   prompt — it starts each invocation with fresh context and cannot see
   the exchange otherwise. Repeat until it produces the spec. Cap this
   at **five rounds**: if the questions have not converged by then, stop
   and ask the user to settle the scope directly.

The product-owner subagent will write `spec.md` and then stop for user
review. Once the user confirms the spec, the next step is `/plan`
(Architect role). Do not start implementing yet.

If the reviewed spec's **Glossary** section pins down new domain terms,
promote them to `development/glossary.md` as part of the review wrap-up
(the product-owner subagent cannot write outside the feature
directory). The glossary is a **register**: promotion from a reviewed
spec is its one sanctioned mid-feature channel (see Document liveness
in `development/harness-usage.md`), and the Reviewer checks each
promoted entry against the spec's Glossary section — so promote the
reviewed terms verbatim, and don't fold in renames or meaning changes
of existing entries (those are trunk-gated, a dedicated PR).
