# CF-10 Batch AH r006 — disposable isolated Copilot HOME (UA)

Мета: виправити можливу причину nonzero exit=1 у Copilot 1.0.107 --version (AH r005: stderr 355 байтів, без розкриття), не розширюючи привілеї.

Root готує єдиний каталог `/run/forprint-cf10-batchad-<unit>/offline-home` з UID=996/GID=992 mode=0700; systemd дозволяє запис лише в цей каталог, залишаючи ProtectSystem=strict, PrivateNetwork=yes, IPAddressDeny=any, RestrictAddressFamilies=AF_UNIX, NoNewPrivileges=yes, PrivateTmp=yes. Дочірній процес отримує лише allowlisted HOME/XDG_CONFIG_HOME/XDG_CACHE_HOME/XDG_DATA_HOME/COPILOT_HOME, жодних токенів, `--version` і відсутність мережі. Вміст каталогу видаляється лише після підтвердженого stop/readback; очищення не проходить за symlink. Раніше успішний синтетичний AE/AG режим без змін.

Це окрема одноразова репетиція на s01. Успіх означає offline `--version` конкретного pinned CLI + Dispatcher nonce + IPC + kernel 1→0. Невдача означає HOLD з метаданими, не виводом stderr. G1–G5 відкриті. Жодного production claim/ledger/inference, push змін джерел лише після тестів, 18 dirty файлів недоторкані.
