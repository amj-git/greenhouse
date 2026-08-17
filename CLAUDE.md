# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Greenhouse temperature/environment logger and control system for Raspberry Pi hardware, with a Kivy touchscreen GUI and a Flask web dashboard. See https://github.com/amj-git/greenhouse/wiki for more background.

## Running the app

There is no package manifest (no `requirements.txt`/`Pipfile`) and no test suite or linter configured in this repo.

- Entry point: `python3 gh_gui.py` (run from the repo root; it loads `gh_gui.kv` via a relative path). `gh_main.py` is currently empty/unused.
- Runtime dependencies to have installed: `kivy`, `flask`, `flask-socketio`, `paho-mqtt`. On Linux/RPi you additionally need `pigpio` (with `pigpiod` running) and `prctl`; these imports are wrapped in `try/except ImportError` so the app still runs without them.
- **Platform-dependent simulation**: on non-Linux platforms (i.e. Windows dev machines) hardware I/O is automatically simulated (`sim_hw=True` in `gh_io.py`), generating random data instead of touching real GPIO/sensors. This is the normal way to develop/test locally on Windows — no RPi hardware is required.
- On a real Raspberry Pi, `pigpiod` must be started first (see `greenhouse.sh`), and the app is normally run as a systemd service — see `gh.service` (copy to `/lib/systemd/system/`, `sudo systemctl enable/start gh.service`).
- The web dashboard is served on port 5000 (`http://<host>:5000/` and `/graph1`) once the app is running.
- `backup_onedrive.sh` backs up the sqlite `db/*.db` files via `rclone` to a remote named `gh_backup_onedrive`; intended to be run from cron.

## Architecture

The system is split into **two OS processes** connected by a `multiprocessing.Queue` (sensor data, one-way) and a `multiprocessing.Pipe` (commands/queries, request-response):

1. **GUI process** (`gh_gui.py`) — the Kivy app. Owns the screens, the SQLite-backed data store, and the Flask web server thread.
2. **IO process** (`gh_io.py`, spawned via `multiprocessing.Process`) — runs `gh_io_main()`, which owns all the hardware I/O threads and never touches Kivy.

### IO process (`gh_io.py`, `io_thread.py`)

- `IO_Thread` (in `io_thread.py`) is the base class for every sensor/actuator. Each hardware device runs in its own thread with a fixed heartbeat `period`, implementing `_startup()`, `_heartbeat(triggertime)`, `_shutdown()`, `_set_op_desc()`. `_heartbeat` pushes readings onto `out_q` as dicts `{tname, time, pname, data}`.
- `IO_Thread_Manager` owns the list of threads, starts/stops them, and creates the shared `IO_Buffer` (`io_buffer.py`) — a per-thread/per-parameter `deque` that lets one thread read another's latest values (used by controller threads).
- A thread can be a "slave" of another (`slave_thread=`) so its heartbeat is triggered manually by the master right before the master's own heartbeat runs — used to keep the grow-light controller and its light sensor in sync (see `io_thread5`/light controller wiring in `gh_io.py`).
- Concrete device threads: `IO_Thread_DS18B20` (1-wire temp, via `io_w1.py`), `IO_Thread_BH1750` (I2C light sensor, `io_bh1750.py`), `IO_Thread_DHT22` (temp/humidity, `io_dht22.py`), `IO_Thread_Moist` (`io_moist.py`).
- Controller threads implement closed-loop control against a target read from another thread's buffer, and expose a small text command protocol (see below): `IO_Thread_Heater` (`io_heater.py`, thermostat + fan with on/off hysteresis timers and fan overrun/prestart), `IO_Thread_Light_Ctrl` (`io_light_ctrl.py`, PWM grow-light integral controller against a target lux), `IO_Thread_Sprinkler` (`io_sprinkler.py`, valve on/off scheduling).
- Each controller supports modes `OFF` / `AUTO` (follows a time-of-day schedule of `[value, start_h, start_m, stop_h, stop_m]` pegs) / `BOOST` (temporary override for N minutes).
- `gh_io_main()`'s loop polls the control `Pipe` for commands and dispatches by string prefix (e.g. `cmd[:6]=='HEATER'` → `io_thread_heater.command(cmd, data)`), and drains `local_io_q` into both the local `IO_Buffer` and the cross-process `io_q`.
- **Command protocol**: commands are plain strings like `'HEATER:MODE'`, `'HEATER:MODE?'`, `'HEATER:BOOST_PARAMS'`, `'HEATER:SCHED_ADD'`, `'LIGHT_CTRL:...'`, `'SPRINK:MODE'`, plus process-level `'OPDESC?'`, `'START'`, `'TERMINATE'`. Query-style commands end in `?` and return a response over the pipe.

### GUI process (`gh_db.py`, `gh_io_dispatcher.py`, `gh_db_manager.py`)

- `gh_db` (`gh_db.py`) spawns the IO process, exposes `send_io_command`/`io_query` (write to / round-trip over the control pipe), and runs a `gh_mon` thread that drains the cross-process `io_q` and hands each data point to `_consumer_fn` → `gh_db_manager` for persistence.
- `gh_io_dispatcher` (`gh_io_dispatcher.py`) subclasses both `gh_db` and Kivy's `EventDispatcher`. Because `gh_mon` runs on a background thread, it cannot touch Kivy widgets directly — it instead queues data onto `_gh_ev_q`, which a Kivy `Clock.schedule_interval` heartbeat drains on the main thread and re-dispatches as the Kivy event `on_io_data`. This is the pattern to follow for **any** cross-thread → Kivy data flow in this codebase.
- `gh_db_manager.py` is the SQLite persistence layer. One `param_db` (and one `.db` file, `db/<ThreadName>-<ParamName>.db` with spaces replaced by `-`) exists per thread/parameter combination. Each db has `raw_data`, a periodically-computed downsampled `comp_data` (avg/min/max per chunk, `Tchunk` default 10 min), and a `meta_data` table storing the parameter description. Values are stored as scaled integers (`val_comp_mult`, chosen by `ptype`) rather than floats.
- `RootWidget.start_io()` in `gh_gui.py` is the wiring point: creates the `gh_io_dispatcher`, pushes saved config to the IO threads, queries `OPDESC?` to get parameter descriptions for every thread (used to build the status grid/graphs generically), then starts event dispatch.

### Home Assistant integration (`gh_mqtt.py`)

- `gh_mqtt` publishes every sensor/controller reading to an MQTT broker using Home Assistant's MQTT Discovery format, so entities appear in HA automatically — generic from `OPDESC?`, same principle as the status grid/graphs/web dashboard. It is read-only/logging only: it does not subscribe to any command topics, so HA cannot control the greenhouse (yet).
- Config lives in `mqtt_config.json` (repo root, gitignored — written with `enabled: false` defaults on first run if missing). Set `enabled: true` and fill in `host`/`port`/`username`/`password` to turn it on; on Home Assistant OS/Supervised, `host` is the HA host running the Mosquitto broker add-on, and `username`/`password` are a dedicated HA user created for this purpose (not anonymous, not the HA login).
- Wired up in `gh_gui.py`'s `RootWidget.start_mqtt()` (called from `gh_gui_app.on_start()` alongside `start_webserver()`), which binds to the same `on_io_data` event everything else in the GUI process uses.
- Topics: state at `<base_topic>/<thread>/<param>/state`, discovery config (retained) at `<discovery_prefix>/sensor/<node_id>/<object_id>/config`, availability (LWT) at `<base_topic>/status`.

### Web dashboard (`gh_webserver.py`)

- `gh_webserver` is a `Thread` (not a separate process) started from the GUI process after IO starts, running Flask + Flask-SocketIO on port 5000. It reuses the same `gh_io_dispatcher`/`gh_db_manager` instances as the Kivy GUI (they share the SQLite handles).
- Routes: `/` (`templates/status.html`, live status grid pushed via the `on_newdata` socket event) and `/graph1` (`templates/graph1.html`, requests raw series via the `get_graph_raw_data` socket event, reading straight from `gh_db_manager`).

### Kivy GUI (`gh_gui.py`, `gh_gui.kv`)

- `gh_gui_app`/`RootWidget` set up a `ScreenManager` with screens: `status_screen` (`IOStatusScreen`, grid driven by `on_io_data`, `gh_io_status_grid.py`), `graph_screen` (`IOGraphScreen`, zoomable/pannable time-series view using `gh_io_graph.py`/`kgraph.py`, with a fixed ladder of zoom spans in `xzoomlevels`/`xtickspacing`), `sprinkler_screen`, `heater_screen`, `lighting_screen` (schedule editors backed by `gh_schedule_edit.py` and the circular time picker in `k_circulardatetimepicker.py`), and `settings_screen` (`gh_io_settings.py`).
- Settings use Kivy's built-in `Settings` framework with custom panels (`gh_SettingsPanel`/`gh_SettingsInterface`) so it scrolls well on a resistive touchscreen, backed by JSON panel definitions `settings_net.json`, `settings_heater.json`, `settings_lighting.json`. `gh_config` (in `gh_io_settings.py`) owns the Kivy `config` object, defaults, and pushes changes down to the IO process via `send_io_command` whenever a setting changes (`on_config_change`).
- Custom reusable Kivy widgets (each paired with rules in `gh_gui.kv`): `k_circulardatetimepicker.py`, `k_circularlayout.py`, `k_floatknob.py`, `k_yesnopopup.py`.
- `process_control.py` (`pr_cont`) is a thin wrapper around `prctl` (Linux only, no-op on Windows) used to set thread/process names so they're identifiable in `htop`.

## Adding a new sensor or actuator

1. Add a class in `io_thread.py` (sensor) or a dedicated `io_*.py` module (controller with a command protocol, following `io_heater.py`/`io_light_ctrl.py`/`io_sprinkler.py`), implementing `_set_op_desc()`, `_startup()`, `_heartbeat()`, `_shutdown()`, and honoring `sim_hw`.
2. Instantiate and `io_manager.add_thread(...)` it in `gh_io_main()` (`gh_io.py`), choosing a unique `threadname` and heartbeat `period`.
3. If it's a controller, add prefix dispatch for its command namespace in `gh_io_main()`'s main loop (`if cmd[:N]=='YOURPREFIX': ...`).
4. The GUI/webserver need no per-sensor changes — the status grid, graphs, and SQLite databases are all built generically from `OPDESC?` (`get_all_op_descriptions()`), keyed by thread name and parameter name.
