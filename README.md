# qca6490 monitor-mode raw TX

Сборка модуля `qca6490.ko` для POCO F5 (marble) с патчем, добавляющим
TX-обработчик monitor-интерфейсу qcacld-3.0.

- Исходники ядра CI клонирует сам: `Pzqqt/android_kernel_xiaomi_marble`, ветка `melt-rebase`.
- В репозитории лежит только патч (`patches/`) и workflow.

Запуск: вкладка **Actions** → *build qca6490.ko* → **Run workflow**.
Результат — артефакт `qca6490-module`: сам `.ko`, `build.config` и `Module.symvers`.

Конфигурация принудительно доводится до ABI работающего ядра:
`LTO_CLANG_FULL`, `CFI_CLANG`, `CFI_CLANG_SHADOW`, `HZ=300`.
Все вызовы make идут с `LLVM=1 LLVM_IAS=1` — без `LLVM_IAS=1`
символ `HAS_LTO_CLANG` в 5.10 недоступен и LTO молча отключается.
