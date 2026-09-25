# Drumless for Max

Программа принимает аудиофайл и сохраняет рядом версию **без ударных**: `название (no drums).wav`. Она использует [Demucs 4.1](https://github.com/adefossez/demucs) для оценки дорожки ударных и вычитает её из исходного микса. Это помогает сохранить вокал и другие инструменты. Разделение готовой песни не бывает идеальным: иногда остаются отдельные удары или появляются артефакты.

Файл обрабатывается локально. При первом запуске скачиваются веса модели; сама песня никуда не загружается. Результат — WAV 24 бит, с исходной частотой дискретизации, тем же числом каналов и длительностью, что у декодированного исходника. Повторного MP3-сжатия нет.

## Windows: установка

1. Установите [Python 3.12 для Windows, 64 бит](https://www.python.org/downloads/release/python-31210/). В установщике включите **Add python.exe to PATH** и **Python Launcher**.
2. Откройте PowerShell и установите FFmpeg:

   ```powershell
   winget install --id Gyan.FFmpeg --exact
   ```

   Закройте и снова откройте PowerShell. Проверьте, что команды `ffmpeg -version` и `ffprobe -version` работают.
3. Скачайте этот проект через **Code → Download ZIP** на GitHub и распакуйте ZIP в удобную папку.
4. Дважды щёлкните `setup_windows.bat`. Он создаст `.venv` в папке проекта и установит зависимости. Для этого нужен интернет.

## Windows: использование

- Перетащите MP3, WAV, FLAC, M4A или другой аудиофайл на `run_windows.bat`.
- Либо дважды щёлкните `run_windows.bat` и выберите файл в открывшемся окне.
- Дождитесь сообщения `Saved: ...`. Готовый WAV появится **рядом с исходным файлом**. Исходник не изменится.

Первый запуск может быть дольше из-за загрузки модели. По умолчанию используется `htdemucs_ft`: он немного точнее базовой модели, но примерно в четыре раза медленнее. Программа использует CUDA только если установленный PyTorch поддерживает вашу NVIDIA GPU; после обычного `setup_windows.bat` рассчитывайте на CPU. Проверка: `.\.venv\Scripts\python.exe -c "import torch; print(torch.cuda.is_available())"`. Для установки версии PyTorch с CUDA следуйте [официальной инструкции PyTorch](https://docs.pytorch.org/get-started/locally/).

Можно запускать через PowerShell, чтобы указать путь к файлу и дополнительные параметры:

```powershell
cd "C:\путь\к\папке_проекта"
.\.venv\Scripts\python.exe .\drumless.py "C:\Music\song.mp3"
```

Более быстрый вариант:

```powershell
.\.venv\Scripts\python.exe .\drumless.py "C:\Music\song.mp3" --model htdemucs
```

Указать имя результата или заменить уже существующий результат:

```powershell
.\.venv\Scripts\python.exe .\drumless.py "C:\Music\song.mp3" --output "C:\Music\song-instrumental.wav" --overwrite
```

Если не хватает видеопамяти, добавьте `--device cpu`. Полный список параметров: `python .\drumless.py --help` внутри активного `.venv` или `.\.venv\Scripts\python.exe .\drumless.py --help`.

## Если что-то не работает

- **`FFmpeg and ffprobe must be installed`** — установите FFmpeg и перезапустите PowerShell либо окно проводника. Проверьте обе команды `ffmpeg -version` и `ffprobe -version`.
- **`py` или Python 3.12 не найден** — установите 64-битный Python 3.12 с Python Launcher, затем снова запустите `setup_windows.bat`.
- **`Output already exists`** — переименуйте готовый файл или запустите программу с `--overwrite`.
- **CUDA out of memory** — попробуйте `--device cpu`.
- **Модель долго работает** — CPU-разделение песни может занять много минут. Для более быстрого результата используйте `--model htdemucs`.

Поддерживаются моно и стерео. Модель Demucs обучена для музыкального разделения; полностью сохранить каждый звук при удалении ударных из готового микса нельзя. [Документация Demucs](https://github.com/adefossez/demucs/blob/main/README.md) и [инструкция для Windows](https://github.com/adefossez/demucs/blob/main/docs/windows.md).
