<!-- jp-web-security-audit v1.0.0 貼り付け版。Agent Skills を読み込めない環境（チャット・API）で、この1ファイルをプロジェクトの知識ファイルに入れるか、会話の最初・システムプロンプトに貼って使う -->
# スキル: jp-web-security-audit（v1.0.0）

以下はひとつのスキルのファイル一式です。最初の SKILL.md の指示に従ってください。
本文が `references/…` などのファイルを読むよう指示したら、下の同じパスの `=== FILE: … ===` の節を読んでください。
スクリプトを実行できない環境では、SKILL.md に書かれた代替の手順で進めてください。

=== FILE: SKILL.md ===
---
name: jp-web-security-audit
description: >-
  コード・API・サービスのセキュリティを、防御側の立場でソースから監査する。日本語の報告書（IPA「安全なウェブサイトの作り方」の項番つき、根本的解決と保険的対策）と、個人情報が漏れたときの個人情報保護委員会への報告の要否・期限（速報・確報）、他社製品の脆弱性の IPA への届出までを扱う。「このコードの脆弱性を見て」「セキュリティ監査して報告書にして」「SQLインジェクションが見つかった、取引先向けにまとめて」「個人情報が漏れたかも、報告は要る？期限は？」「令和8年の個人情報保護法改正で漏えい報告はどう変わる？」と頼まれたときに使う。Keywords: security audit, vulnerability review, pen test, 脆弱性診断, セキュリティ監査, 個人情報漏えい, 漏えい等報告。本番環境や他者のシステムへの攻撃・侵入、マルウェア作成は対象外。
license: MIT
metadata:
  version: "1.0.0"
  author: frametech
---

# Security Audit（日本向け）

元: https://github.com/cloudflare/security-audit-skill@c1c8a8c（MIT、`LICENSE`）を改変。日本の組織・日本語の報告向けの規則（[references/JAPAN.md](references/JAPAN.md)）を追加。

**日本の組織のシステム、日本語での報告、個人情報の漏えい、他社製品の脆弱性の届出が関わるときは、[references/JAPAN.md](references/JAPAN.md) を読んでから出力する。** 法令の結論は断定せず、根拠と確認事項を示す。

Find vulnerabilities that violate a real trust boundary, then give owners the source evidence, safe reproduction, priority, and smallest effective fix. This is a defensive, source-first workflow. A candidate without a concrete affected principal, resource, or security outcome is not a confirmed finding.

## Operating modes

This skill is guidance by default. Loading it does not authorize the complete audit workflow or file creation.

- **Guidance mode**: For security questions, focused reviews, methodology, triage, or investigation of specific findings, use only the relevant parts of this skill. Do not automatically run all six phases, create an output directory, or write audit artifacts. You may launch focused agents when useful; they return results to the current task.
- **Full audit mode**: Use the complete workflow when the user explicitly asks to audit or pen-test a codebase, asks for a full, comprehensive, or end-to-end security review, or requests report artifacts. Run all six phases and write the files defined below.

If the request could mean either mode, ask one focused question before creating files or starting the complete workflow.

## Platform terminology

This skill is agent-neutral:

- **Parent** is the agent that coordinates the run and owns shared state.
- **Task tool** is the platform's delegation or sub-agent mechanism.
- **`research` agent** is a delegated agent for focused source exploration and factual verification.
- **`general` agent** is a delegated agent for broad investigation and bounded local execution.
- **`subagent_type:`** in a heading names which of these two delegated agent roles runs that work.

Use equivalent platform capabilities while preserving role, write-isolation, prompt, and independence boundaries.

## Universal execution safety

These rules apply in both operating modes. Source inspection is read-only. Run target-controlled builds, tests, processes, browsers, emulators, fuzzers, and fixture processing only inside an OS-enforced sandbox that provides all of these controls:

- no external network; use only an isolated loopback namespace when the check needs local client/server traffic;
- an empty environment populated from an explicit allowlist with safe values, with scratch-local `HOME`, temporary directories, and caches;
- a read-only target and toolchain, with the target-controlled process able to write only inside its assigned `scratch/` directory; and
- explicit low CPU, memory, process, file-size, disk, and wall-clock limits.

The agent, outside the target-controlled process, may make a disposable source copy in an assigned `scratch/` directory when a build must write beside source. In guidance mode, do not retain target-controlled files. In full audit mode, only trusted parent-side code may promote the minimum non-secret result to retained `artifacts/` using the procedure under Write isolation. Never expose a retained output directory (other than the agent's own assigned `scratch/`), another agent's directory, the host home directory, credentials, sockets, or shared services to target code. Do not install dependencies or let builds fetch them. Use only tools and dependencies already available locally. If every control cannot be enforced, do not execute target code: report the missing sandbox capability as a needs-validation blocker and give a safe validation plan.

Use dummy principals, fixtures, and secrets. Do not probe deployed endpoints, external services, shared infrastructure, production identities, other users' data, or live control planes. Do not test availability against a live or shared process, publish artifacts, alter releases, spend paid API quota, or continue beyond the minimum local effect needed to establish a defect. If the decisive fact is outside source or the sandboxed fixture, report it as needing validation.

## Full audit setup

In full audit mode, resolve these values before reconnaissance:

- **Skill directory**: the absolute directory containing this `SKILL.md`.
- **Target**: the absolute repository root under review.
- **Repo name**: a stable repository identifier from the directory or local Git remote.
- **Output directory**: a new writable directory outside the target, defaulting to `~/security-audit-skill/<repo-name>/run-<N>`, where `<N>` is the next unused integer. Use a directory inside the target only when the user explicitly selects it and the parent verifies that version control ignores the whole directory. Otherwise stop and request an external path.
- **Source ref**: the reviewed commit and whether the worktree is dirty. Do not treat unreviewed generated or modified files as another revision.

### Write isolation

The parent creates and is the only writer of shared run files:

- `run-metadata.json`
- `architecture.md`
- `coverage-ledger.json`
- `findings.json`
- `REPORT.md`
- `FINDINGS-DETAIL.md`
- `NEEDS-VALIDATION.md`

Each hunter or verifier receives a unique root under `<output-dir>/agents/<agent-id>/`, with separate `scratch/` and `artifacts/` directories. Canonical agent IDs match `^[a-z0-9][a-z0-9_-]{0,63}$` and must not equal a Windows device name such as `con`, `prn`, `aux`, `nul`, `com1` through `com9`, or `lpt1` through `lpt9`. Lowercase IDs prevent case-fold collisions. The agent and every target-controlled process may write only to `scratch/`; retained `artifacts/` is parent-owned, is never exposed to the sandbox, and is writable only by trusted parent-side promotion code. Agents may not change shared files, target source, retained artifacts, or another agent's directory. Do not use `/tmp` or the host home directory as a writable fallback.

Before execution, the parent opens and retains trusted, non-inheritable directory descriptors for the agent's `scratch/` and `artifacts/` roots, and records an allowlist of expected scratch-relative artifact files plus explicit per-file and cumulative byte limits. Never pass those descriptors to the agent or sandbox. After the sandbox and all its processes terminate, trusted parent-side code promotes each allowlisted file separately:

1. Validate the declared relative path: reject absolute, empty, `.`, `..`, or symlinked components.
2. Walk each parent component from the retained scratch-root descriptor with no-follow directory-relative operations; never reopen by path.
3. Open the leaf no-follow and nonblocking.
4. Verify with `fstat` that it is a regular file with link count exactly one and within the recorded per-file and cumulative byte limits.
5. Enforce those limits again while reading from that descriptor.
6. Copy exactly the verified size, repeat `fstat`, and reject a changed identity, type, link count, or size.
7. For the destination, walk every parent component from the retained artifacts-root descriptor with no-follow directory-relative operations; require each existing component to be a real directory, and create any missing directory exclusively before reopening and verifying it no-follow.
8. Create the leaf exclusively without following links, verify that the opened destination is a regular file with link count exactly one, and copy from the verified source descriptor without reopening either path.
9. Use equivalent race-safe APIs on non-POSIX systems.
10. Never recursively copy or glob scratch, extract an archive into artifacts, or open or promote a symlink, FIFO, socket, device, directory, hard-linked file, changing file, or file that exceeds its bound.
11. If any check is unavailable, cannot be enforced, or fails, discard the scratch entry; if it is decisive evidence, retain `needs_validation` with the exact promotion blocker.

[HUNTING.md](HUNTING.md) and [VALIDATION-AND-REPORTING.md](VALIDATION-AND-REPORTING.md) carry this procedure as one identical fenced block for hunter and verifier prompts; it states the same rules in the same order as this list.

For a reproduced check, record the command, exact test input, sandbox limits, and only the allowlisted environment variable names plus safe non-secret values needed to reproduce it. Never capture or copy the ambient environment, inherited variables, credential values, authentication state, or unrelated host paths. Launch from an empty environment rather than trying to redact one after execution.

Before delegation, the parent writes `run-metadata.json` with at least `run_id`, `repo`, `target`, `source_ref`, `profile`, `scope_paths`, `budget` (null if unset), `execution_policy: "sandboxed-source-and-local-only"`, selected companion files, prior-run paths, shared-file owners, and `run_status: "in_progress"`. Update metadata only when those facts change; candidate state belongs in the coverage ledger and `findings.json`.

## Full audit planning

The coverage, prior-run, profile, and budget requirements in this section apply only in full audit mode.

### Coverage and prior runs

No one pass is complete. Build a deterministic coverage plan before hunting and update it after every agent result. [RECONNAISSANCE.md](RECONNAISSANCE.md) defines the stable coverage units and [HUNTING.md](HUNTING.md) defines coverage-critic waves. The parent alone updates the ledger.

If prior runs exist, read every compatible `coverage-ledger.json` and `findings.json` before planning the current run:

1. Compare the relevant current source with each prior record and unit. A prior source ref alone is not evidence that a path is unchanged.
2. Carry a prior `confirmed` record into the current candidate set only when its relevant source and conditions are unchanged and its evidence still meets the current contract. Link it to a current ledger unit seeded `planned`, preserve its fingerprint, exclude only that carried root cause from hunters, and send the carried record through the current final verification path; the Phase 3 verifier that re-checks it becomes that unit's assignment owner and moves it to `candidate`.
3. When relevant source for a prior `confirmed` record changed, create a current planned revalidation unit. Do not put that record on the hunter exclusion list. It remains confirmed only if current independent validation establishes the current path and result.
4. Make prior `needs_validation`, `deferred`, `blocked`, `out_of_scope`, and any changed-source unit current work. A still-external `needs_validation` record may be carried only after the current source trace is checked and linked by fingerprint to a current `planned` unit whose verifier re-check supplies its owner and evidence; the record keeps the unresolved blocker. These prior states never suppress a current unit.
5. A prior same-source covered unit may inform priority, but it remains visible in the current ledger. A prior `rejected` record suppresses only the unchanged failed claim, not coverage of its unit; changed evidence creates current work.
6. Read the prior profile and scope. A prior `quick` or scoped ledger contributes only its recorded evidence and gaps, never an implied "rest is fine."

If no prior ledger exists, say so in the final coverage statement. Never imply that one run exhausts the target.

### Run profiles and scope

During full audit setup, pick a profile from the user's request or propose one from the target's size and stakes. Record it in `run-metadata.json` (`profile`, `scope_paths`) and state it in the report. The default is `standard`.

- **`quick`** — a bounded pass for small targets, re-runs, or a fast first look. Coarsen ledger units to surface × boundary × attack class (subsystem uses the fixed canonical `profile/quick/all-in-scope-subsystems` identifier), run exactly one hunter wave followed by exactly one final coverage-critic pass, and use one fresh verifier per candidate for both candidate validation and final record verification. Do not launch a follow-up hunter wave: record the critic's accepted discoveries and reassignments as `deferred`.
- **`standard`** — the workflow as written.
- **`deep`** — for high-stakes or large targets. Split ledger units per subsystem and lifecycle mode, run critic waves to a clean pass, keep candidate validation and final record verification as separate fresh agents, and give `prior_covered_same_source` units an independent second pass.

A **scoped run** audits a subset: named paths, one subsystem, one companion domain, or the diff between two source refs. Seed ledger units only for in-scope surfaces and record everything else as `out_of_scope` — never as `covered`. A scoped or `quick` run must present itself as partial coverage.

Profiles change breadth and redundancy, never the evidence bar. Do not scale away the candidate gate, the source/local execution boundary, `needs_validation` discipline, schema validation, or independent verification of `confirmed` records.

#### Cost budget

The ledger makes spend countable: one unit is roughly one hunter assignment, and one surviving candidate is one or two verifier assignments depending on profile. When the user sets a budget — or the parent proposes one for a large target — record `budget` in `run-metadata.json` as a maximum number of agent invocations across all phases.

Apply the strict budget gate before launching any reconnaissance agent. Reserve the four baseline reconnaissance calls, one final post-wave critic for `quick` or one post-wave plus one distinct final-clean critic for `standard`/`deep`, and at least one verifier call. Add focused reconnaissance only after repeating this gate for each extra call. If the requested budget cannot fund that minimum, launch no agent: ask for a larger budget, narrower scope, or different profile. If the request remains unchanged, set `run_status: "incomplete"` with `incomplete_reason: "budget_cannot_fund_reconnaissance_and_reserves"` and report that no audit pass ran.

Spend it in this order:

1. Count reconnaissance, every post-wave critic, and the separate final-clean critic as agent invocations.
2. **Reserve critics and validation before hunting.** For `quick`, reserve its one post-wave final critic. Before every `standard` or `deep` hunter wave, reserve one immediate post-wave critic plus one distinct final-clean critic. Also reserve verifier cost from the profile (about 1 or 2 agents per expected candidate; when in doubt reserve 30% of the balance after critic reservation). Never assign hunters into either reserve.
3. Assign hunters to units in priority order until the hunting allowance is spent. Spend the reserved post-wave critic immediately after that wave; keep the final-clean and validation reserves intact.
4. Before a later wave, reserve its new post-wave critic again. If the remaining budget cannot cover the required critic calls and validation reserve, launch no hunters from that wave, mark its planned units `deferred` with reason `budget_cannot_reserve_critics_and_validation`, and use the retained final-clean critic to record the resulting gap.

Before wave 1, update the pre-recon estimate with seeded units, implied hunter count, mandatory critic calls, validation reserve, and whether the remaining budget covers the plan. If it clearly cannot, say so and propose either a tighter scope or a coarser profile instead of silently thinning evidence. If later facts consume the required final-critic reserve, launch no hunters, mark all planned work deferred, set the run incomplete with reason `critic_budget_exhausted`, and make no complete-coverage claim.

A strict total-agent budget can still be exceeded by an unexpectedly large candidate set or by a material Phase 5 replacement that needs another independent verifier. If the remaining budget cannot validate every candidate, stop hunting, validate candidates in fingerprint order while the budget permits, and set `run_status: "incomplete"` plus `incomplete_reason: "validation_budget_exhausted"`. Keep each unvalidated fingerprint linked to a `candidate` ledger unit with that unresolved reason. Do not put an unvalidated candidate in `findings.json`, relabel it `needs_validation`, or report the run as complete. Phase 6 may produce a partial report only if its first section states that candidate validation is incomplete and lists the affected fingerprints and units. Never exceed a user-set strict budget silently.

## Core principles

### Require a boundary and result

For every candidate, name the lower-trust principal, accepted input or action, intended control, crossed boundary, affected principal or resource, and concrete observed or owner-observable result. Do not elevate a missing best practice, guessed deployment behavior, generic parser crash, or self-impact into a security finding.

### Use bounded local evidence

Static analysis establishes the source path. Sandboxed local tests resolve behavior when all execution controls are available: a minimal function harness, existing unit test, small parser fixture, dummy-tenant integration test, locally rendered configuration, or bounded isolated-loopback client. Stop at a wrong return value, unauthorized dummy record, sanitizer finding, policy difference, or other minimum effect. Do not extend the local check beyond the minimum boundary result or produce persistence, post-fault, or concealment material.

### Respect source visibility

Deployment controls, proxy behavior, provider settings, browser headers, identity policy, broker ACLs, packaging, and topology are real controls. If they are required and absent from the repository, do not assume either presence or absence. Use `needs_validation` with the exact missing fact and a safe owner-observed or local plan.

### Separate priority from certainty

Only `confirmed` records receive severity. Likelihood and impact must reflect the demonstrated conditions and result; overall severity cannot exceed demonstrated impact. `needs_validation` means a specific source-grounded boundary hypothesis is blocked, not a low-confidence confirmed vulnerability, and it has no severity.

Calibrate overall severity with these anchors:

- **critical** — an unauthenticated actor gains code execution, full data-store access, or takeover of arbitrary accounts.
- **high** — an actor fully defeats an explicit security control with real consequences: authentication bypass, cross-tenant read or write, stored script execution affecting other users, authenticated code execution, or an unauthenticated remote stop of a shared service.
- **medium** — a real boundary violation with limited blast radius, uncommon preconditions, or consequences confined to a narrow resource set.
- **low** — disclosure of non-secret internals, or an effect requiring sustained effort for minimal gain.
- **informational** — a confirmed but minimal-impact observation, useful mainly as a prerequisite inside a larger finding.

The high/medium discriminator: does the demonstrated result fully defeat an explicit control for an action with real consequences, or only weaken it? If you cannot state the concrete damage, the severity is lower than it feels.

### Recommend the smallest effective source fix

For each confirmed finding, identify the invariant the code must enforce and the narrowest source change that enforces it at the last trusted decision point. Prefer specific repository-relative changes and regression tests over generic hardening advice. The audit describes fixes; it does not modify target source.

## Full audit workflow

In full audit mode, follow all six phases in order:

1. **Reconnaissance** — map the source, trust boundaries, local build paths, companion selections, prior evidence, and initial deterministic coverage ledger with [RECONNAISSANCE.md](RECONNAISSANCE.md).
2. **Coverage-led hunting waves** — assign isolated hunters from the ledger and collect structured candidate results with [HUNTING.md](HUNTING.md), [ATTACK-CLASSES.md](ATTACK-CLASSES.md), and the selected domain companions.
3. **Candidate validation** — consolidate fingerprints and give every candidate to a fresh source verifier as defined in [VALIDATION-AND-REPORTING.md](VALIDATION-AND-REPORTING.md).
4. **Structured output** — write all final `confirmed`, `needs_validation`, and `rejected` records to `findings.json`; validate it with `report-schema.json` and `validate-findings.cjs`, and validate the coverage claim with `validate-coverage-ledger.cjs`.
5. **Independent record verification** — use fresh agents to verify final source claims and reconcile corrections or state changes.
6. **Target-neutral report** — derive `REPORT.md`, `FINDINGS-DETAIL.md`, and `NEEDS-VALIDATION.md` from the final records, with no live-probe instructions.

Do not end the run before one of exactly two terminal states: (a) all Phase 6 artifacts are written and both validators pass, or (b) `run_status: "incomplete"` is recorded with its exact reason and the gap is disclosed in the report. Never stop mid-phase.

## Anti-patterns

1. Checklist deviations presented as vulnerabilities.
2. Defense-in-depth advice with no reachable boundary violation.
3. Live or shared-environment testing where bounded local evidence is insufficient.
4. Guessing provider, proxy, browser, identity, or deployment behavior not present in source.
5. Treating intended same-principal authority or self-impact as a cross-boundary result.
6. Reporting a parser or runtime effect stronger than the observed effect.
7. Emitting prose-only hunter results that cannot be deduplicated or verified.
8. Re-reporting carried same-source prior confirmed records or using them as exemplars that anchor the hunt.
9. Assigning severity to `needs_validation` records.
10. Writing the report before independent verification or letting prose and JSON disagree.

=== FILE: references/JAPAN.md ===
# 日本の組織・日本語の報告で使うときの追加規則

日本の組織のシステムを監査するとき、日本語で報告するとき、個人情報の漏えいや他社製品の脆弱性が関わるときに読む。SKILL.md の手順（境界と結果を示す、ローカルで最小限に確かめる、重大度の付け方）はそのまま守り、出力と事後対応にこの規則を足す。

**ここに書いた法令・制度は変わる。確認日（2026-10-10）から90日を過ぎたら、§5 の公式ページを読み直してから使う。** 法的な結論は出さない。根拠の条文・公式ページと、該当しうる箇所を示し、「最終判断は社内の法務・個人情報保護の担当者が行う」と添える。

## 1. 日本語の報告書

- 確認済み（`confirmed`）の指摘ごとに、IPA「安全なウェブサイトの作り方」（改訂第7版）の項番を併記する。当てはまる項番が無いものは「該当項番なし」と書き、CWE を併記する

| 項番 | 脆弱性 |
|---|---|
| 1.1 | SQLインジェクション |
| 1.2 | OSコマンド・インジェクション |
| 1.3 | パス名パラメータの未チェック／ディレクトリ・トラバーサル |
| 1.4 | セッション管理の不備 |
| 1.5 | クロスサイト・スクリプティング |
| 1.6 | CSRF（クロスサイト・リクエスト・フォージェリ） |
| 1.7 | HTTPヘッダ・インジェクション |
| 1.8 | メールヘッダ・インジェクション |
| 1.9 | クリックジャッキング |
| 1.10 | バッファオーバーフロー |
| 1.11 | アクセス制御や認可制御の欠落 |

（IPA の注記: 項番は対策の優先順位ではない。優先順位は SKILL.md の重大度で付ける）

- 修正案は IPA の用語に合わせて「根本的解決」（原因をなくす変更）と「保険的対策」（影響を減らす変更）に分ける。SKILL.md の「最小の効果的な修正」は根本的解決に当たる
- 重大度の訳語: critical＝緊急、high＝重要、medium＝警告、low＝注意、informational＝情報。英語の値（`findings.json`）は変えない
- 指摘1件の書き方（日本語の REPORT.md・回答で使う）:

```text
【重要】SQLインジェクション（IPA 1.1／CWE-89）
場所: src/api/users.ts:42（検索語を文字列連結で SQL に入れている）
起きること: 未ログインの利用者が、他の会員のメールアドレスを読み出せる（ローカルの検証用DBで確認）
根本的解決: プレースホルダ（バインド変数）で SQL を組み立てる
保険的対策: DB ユーザーの権限を読み取り専用に絞る
個人情報: 会員のメールアドレスを含む → §2 の報告要否を確認
```

## 2. 個人情報が漏えいした・漏えいしたおそれがあるとき（個人情報保護法）

確認済みの指摘で、個人データが第三者に読まれた・読まれうる状態だったときは、報告書の末尾にこの節の確認事項を付ける。

**委員会への報告が義務になる事態**（個人情報の保護に関する法律施行規則 第7条。民間事業者。どれか1つに当たれば報告）:

1. 要配慮個人情報（病歴・健康診断の結果・犯罪の経歴など）を含む個人データの漏えい等（高度な暗号化などの保護措置をしたものを除く）
2. 不正に利用されると財産的被害が生じるおそれがある個人データ（クレジットカード番号、送金・決済できるサービスの ID とパスワードの組合せなど）
3. 不正の目的をもって行われたおそれがある行為による漏えい等（外部からの不正アクセス、ランサムウェア、従業者による持ち出し、Web サイトの改ざんで入力情報が送られた場合など）
4. 本人の数が1,000人を超える漏えい等

いずれも「発生したおそれ」の段階で対象になる。

**期限**（同規則 第8条、ガイドライン通則編 3-5-3-3）:

| 報告 | 期限 |
|---|---|
| 速報 | 事態を知った後、速やかに（目安は**概ね3〜5日以内**。法人はいずれかの部署が知った時点から数える） |
| 確報 | 事態を知った日から**30日以内**。上の3（不正の目的）に当たるときは**60日以内** |

- 報告は個人情報保護委員会の Web の報告フォームから。委託先は、委託元へ速やかに通知すれば報告義務を免れる（その場合は委託元が報告する）
- 報告義務があるときは、原則として本人への通知も要る（通知が困難な場合は公表などの代替措置）
- ランサムウェアによる漏えい等は、令和7年10月1日以降、政府のサイバー攻撃被害報告の共通様式でも報告できる。その他のサイバー攻撃による漏えい等も、令和8年10月1日以降、共通様式で報告できる

**令和8年の改正（未施行）**: 令和8年7月17日に公布され、施行は公布から2年を超えない範囲で政令が定める日。政令・規則・ガイドラインは検討中（2026-10-10 時点）。**施行されるまでは上の現行ルールで判断する。** 漏えい対応に関わる改正点:

- 本人の権利利益の保護に欠けるおそれが少ない場合（例: それ単体ではほぼ意味を持たない社内 ID だけの漏えい）は、本人通知を代替措置で済ませられるようにする
- 認定個人情報保護団体などの確認を前提に、一定の範囲で速報を免除できるようにする。本人1名の誤送付・誤交付は、確報をまとめて出すことを許す
- 違法な個人データの第三者提供も報告対象にする
- 重大な違反に課徴金を導入する

## 3. 他社のソフトウェア製品・Web サイトに脆弱性を見つけたとき

- 自社の対象外（他社の製品・OSS・他社サイト）の脆弱性は、**公表せず**、IPA の「脆弱性関連情報の届出」に届け出る。IPA が受け付け、ソフトウェア製品は JPCERT/CC が開発者と調整し、公表は調整のあとに行われる
- 届け出る前に、他社の本番環境で確かめない（SKILL.md の実行の安全規則と同じ）
- 届け出る内容は、対象・再現条件・影響と、ローカルで確かめた最小の証拠まで

## 4. 書き方の注意

- 法令名・条文番号・期限は §2 の表から写す。記憶で書かない
- 「報告は不要です」と断定しない。「施行規則第7条の各号に当たる事実は今のところ見当たらない。次の点が分かれば判断できる」の形にする
- 日付は和暦と西暦を混ぜない（ページ内でどちらかに統一）

## 5. 出典（確認日 2026-10-10）

- IPA「安全なウェブサイトの作り方」: https://www.ipa.go.jp/security/vuln/websecurity/about.html
- e-Gov 法令検索「個人情報の保護に関する法律施行規則」第7条・第8条: https://laws.e-gov.go.jp/law/428M60020000003
- 個人情報保護委員会「漏えい等の対応とお役立ち資料」: https://www.ppc.go.jp/personalinfo/legal/leakAction/
- 個人情報保護委員会「個人情報の保護に関する法律についてのガイドライン（通則編）」: https://www.ppc.go.jp/personalinfo/legal/guidelines_tsusoku/
- 個人情報保護委員会「令和８年 改正個人情報保護法について」と概要資料: https://www.ppc.go.jp/personalinfo/legal/r8kaiseihogohou/
- IPA「脆弱性関連情報についての届出」: https://www.ipa.go.jp/security/todokede/vuln/index.html

=== FILE: LICENSE ===
MIT License

Copyright (c) 2025-2026 Cloudflare, Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
