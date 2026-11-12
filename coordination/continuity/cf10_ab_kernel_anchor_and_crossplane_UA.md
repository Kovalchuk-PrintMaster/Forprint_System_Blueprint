# CF-10 AB — Canonical kernel anchor та cross-plane readiness

## Мета

Після Batch AA (`feccb10a9f47b8c460285dde83d0abce333fd96c`) виконати цілісне посилення першого Worker без нового launcher, паралельного Dispatcher або відкриття live cutover. Не дублювати W/X, R140 та вже доведені лабораторії TLS.

## Конкретна зміна

У канонічному `cf10_systemd_kernel_witness_v0_1.py` закріплюється inode каталогу cgroup **до** відкриття `cgroup.events`. Другий FD утримується до `KernelWitness.close()`. `fstat` і первісний `lstat` звіряються за dev/inode та UID=0. Events відкривається відносно dirfd з `O_NOFOLLOW`; при будь-якому HOLD обидва FD закриваються. Це підсилює життєвий цикл pinned witness і захист від підміни шляху.

Гіпотеза: додатковий dirfd може зменшити ризик втрати kernel event inode при швидкій terminalization, спостережений у Batch T. **Це не доводить**, що Linux дозволить читати inode після видалення cgroup, і не є гарантією вирішення Batch T. Позитивний локальний тест звичайної файлової системи не замінює живий cgroup v2 тест на s01.

## Canonical cross-plane gate

Новий `make cf10-first-worker-crossplane-gate-check` не містить власних Dispatcher, lifecycle-ledger чи provider adapter. Він викликає наявні:

- `cf10_training_dispatch.resolve_training_task` для реального матеріалізованого тестового task;
- `cf10_first_worker_critical_path.source_check`;
- `cf10_r129_canonical_lifecycle_convergence.synthetic_fixture` та `.convergence` (11 подій; лише source-only);
- `cf10_systemd_launcher_v0_1.LIVE_CUTOVER_ENABLED` (зобов'язаний залишитися False);
- перевірку фактичного поля `KernelWitness.anchor_fd`.

Узгоджена машинна відповідь забороняє помилково вважати source-only lifecycle live execution. Негативні тести перевіряють зміни attempt/task authority, synthetic source status, ledger, 11-крокового trace, source review та live switch.

## Межі виконання

Batch AB не запускає `systemd-run`, не читає credentials, не відкриває provider egress, не споживає claim і не пише production ledger. Код розміщується у git-tracked канонічних файлах; `tmp/` використовується лише для одноразового отримання/тесту та evidence. `AGENTS.md` та 18 локальних змін не перезаписуються. Hestia та sudoers не змінюються. Commit/push виконується лише після всіх тестів і preflight; при HOLD до commit rollback лише власних файлів.

## Що далі

1. Зв'язати справжній root-held kernel anchor з канонічним Dispatcher attempt, не дублюючи код R129.
2. В окремій дозволеній live-спробі довести 1→0 **до** systemctl stop, і після цього — retained systemd readback.
3. Окремо завершити модель provider auth/secret nonexposure та реальний контрольований egress. Простий root-only token file не доводить безпеки Copilot child tools.
4. Перший bounded read-only Copilot inference — лише після отримання незалежних G1/G2 та джерельно пов'язаної owner authorization.
5. Після першого реального Worker: result validation → terminal ledger → незалежний review → next task.

Значення G1–G5 залишаються OPEN. Позитивний Make-check не є підставою змінювати це рішення.


## AC recovery / 2026-11-12

AB evidence: початковий тест R034 `test_terminal_observer_armed_before_ledger` FAIL 1/648 через тестовий mock, що не враховував канонічний R138.review_success; AB код не встановлено. AC інтегрує exact pinned виправлення R034 із AB kernel-directory-FD та crossplane. До commit: усі історичні й нові тести мають PASS. У разі HOLD — без live claims.
