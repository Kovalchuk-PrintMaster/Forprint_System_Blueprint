# CF-10 R083 · Epoch-bound frozen provider provenance

R082 сформував source-bound provider freeze до ACK. R083 закриває downgrade: відсутність обох маркерів не означає, що нова спроба автоматично є історичною. Git ancestry відносно коміту введення R082 (`0282218d998b5d0687323016339081a68724b558`) визначає джерельну епоху.

- HEAD R082 і нащадки: обидва маркери обов'язкові, R082 verify_decision працює повністю.
- Доведені предки R082: лише legacy Copilot/auto, без змішаних схем; це не право повторного запуску.
- Divergent або відсутній commit: FAIL-CLOSED.
- Перевірка запускається до owner claim у canonical pilot preflight та повторюється при переході до PAM; окрема перевірка на launch_cycle. Root-controlled R055 corridor перевіряє те саме до пароля і після owner claim, а source guard pin-ить його нові залежності.
- Жодного нового провайдера, дозволу dispatch чи запису receipts/ledger.

Межі: перевірка Git ancestry не засвідчує незалежне походження доказів і не замінює root receipts, PAM, systemd та незалежну фіналізацію. R083 — source-only hardening, а не завершений мультипровайдерний запуск.
