#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Брахма-мухурта: Подольск 2026, восход и закат по эфемеридам.

Python >= 3.10. Установка: python -m pip install pyswisseph tzdata

Исходные принципы:
    Fixed:     [sunrise - 96 min, sunrise - 48 min]
    Night/15:  [sunrise - 2*(night/15), sunrise - night/15]
где night = sunrise(today) - sunset(yesterday), измеренное в UTC.

Стиль восхода:
    hindu:     центр Солнца на математическом горизонте без рефракции;
    apparent:  верхний край солнечного диска с атмосферной рефракцией.

ВНИМАНИЕ: 48-минутный и пропорциональный методы представляют
разные традиции отсчёта, а не две численные оценки одного интервала.
Используемый 'горизонт' идеализированный, без рельефа и зданий.
"""
from __future__ import annotations

import argparse
import csv
import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

try:
    import swisseph as swe
except ImportError:
    raise SystemExit("Установите зависимость: python -m pip install pyswisseph tzdata")

UTC = timezone.utc
JD_UNIX_EPOCH = 2440587.5
RU_WEEKDAYS = ("понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье")


def julian_day(dt: datetime) -> float:
    """UT-календарная дата в юлианских днях (UTC ≈ UT1 на уровне секунд)."""
    if dt.tzinfo is None:
        raise ValueError("Требуется datetime с явно заданной временной зоной")
    return JD_UNIX_EPOCH + dt.astimezone(UTC).timestamp() / 86400.0


def utc_from_jd(jd: float) -> datetime:
    return datetime.fromtimestamp((jd - JD_UNIX_EPOCH) * 86400.0, tz=UTC)


def next_sun_event(
    local_date: date, event: str, tz: ZoneInfo,
    longitude: float, latitude: float, elevation_m: float,
    sunrise_mode: str,
) -> datetime:
    """Событие восход/закат в заданную МЕСТНУЮ дату, возвращает UTC."""
    local_midnight = datetime.combine(local_date, time.min, tzinfo=tz)
    start_utc = local_midnight.astimezone(UTC)
    event_flag = swe.CALC_RISE if event == "rise" else swe.CALC_SET
    if sunrise_mode == "hindu":
        event_flag |= swe.BIT_HINDU_RISING
    # FLG_MOSEPH: встроенная аналитическая эфемерида, внешних файлов не требует.
    try:
        result, instants = swe.rise_trans(
            julian_day(start_utc), swe.SUN, event_flag,
            (longitude, latitude, elevation_m),
            0.0, 10.0, swe.FLG_MOSEPH,
        )
    except swe.Error as exc:
        raise RuntimeError(f"Не удалось рассчитать {event} {local_date}: {exc}") from exc
    if result != 0:
        raise RuntimeError(
            f"Солнечное событие {event} для {local_date} не найдено; "
            "высокая широта / полярный день или ночь."
        )
    event_utc = utc_from_jd(instants[0])
    event_local = event_utc.astimezone(tz)
    if event_local.date() != local_date:
        raise RuntimeError(
            f"Найдена дата {event_local.date()} вместо {local_date} "
            f"для события {event}; остановлено, чтобы не выдавать неверные данные."
        )
    return event_utc


def local_hhmm(dt_utc: datetime, tz: ZoneInfo) -> str:
    # Календарь в минутах; округление до ближайшей минуты.
    local = (dt_utc + timedelta(seconds=30)).astimezone(tz)
    return local.strftime("%H:%M")


def calculate_one(
    day: date, tz: ZoneInfo, longitude: float, latitude: float,
    elevation_m: float, sunrise_mode: str, place: str,
) -> dict[str, str]:
    previous_day = day - timedelta(days=1)
    prev_sunset = next_sun_event(
        previous_day, "set", tz, longitude, latitude, elevation_m, sunrise_mode
    )
    sunrise = next_sun_event(day, "rise", tz, longitude, latitude, elevation_m, sunrise_mode)
    night = sunrise - prev_sunset  # UTC, корректно и при смене летнего времени.
    if not timedelta(hours=1) < night < timedelta(hours=23):
        raise RuntimeError(f"Недопустимая длительность ночи {night} для {day}")
    one_fifteenth = night / 15
    dynamic_begin = sunrise - 2 * one_fifteenth
    dynamic_end = sunrise - one_fifteenth
    fixed_begin = sunrise - timedelta(minutes=96)
    fixed_end = sunrise - timedelta(minutes=48)
    local = lambda dt: dt.astimezone(tz)
    return {
        "date": day.isoformat(),
        "weekday_ru": RU_WEEKDAYS[day.weekday()],
        "place": place,
        "latitude_deg": f"{latitude:.6f}",
        "longitude_deg": f"{longitude:.6f}",
        "elevation_m": f"{elevation_m:.1f}",
        "timezone": tz.key,
        "sunrise_convention": sunrise_mode,
        "prev_sunset_local": local_hhmm(prev_sunset, tz),
        "sunrise_local": local_hhmm(sunrise, tz),
        "night_duration_minutes": f"{night.total_seconds() / 60:.2f}",
        "night_muhurta_minutes": f"{one_fifteenth.total_seconds() / 60:.2f}",
        "brahma_night15_start": local_hhmm(dynamic_begin, tz),
        "brahma_night15_end": local_hhmm(dynamic_end, tz),
        "brahma_fixed48_start": local_hhmm(fixed_begin, tz),
        "brahma_fixed48_end": local_hhmm(fixed_end, tz),
        "sunrise_iso": local(sunrise).isoformat(timespec="seconds"),
        "night15_start_iso": local(dynamic_begin).isoformat(timespec="seconds"),
        "night15_end_iso": local(dynamic_end).isoformat(timespec="seconds"),
        "fixed48_start_iso": local(fixed_begin).isoformat(timespec="seconds"),
        "fixed48_end_iso": local(fixed_end).isoformat(timespec="seconds"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Календарь Брахма-мухурты: два метода, учёт астрономии и часового пояса."
    )
    parser.add_argument("--start", type=date.fromisoformat, default=date(2026, 10, 22))
    parser.add_argument("--end", type=date.fromisoformat, default=date(2026, 12, 31))
    parser.add_argument("--place", default="Подольск, Московская область, Россия")
    parser.add_argument("--latitude", type=float, default=55.42419)
    parser.add_argument("--longitude", type=float, default=37.55472)
    parser.add_argument("--elevation", type=float, default=162.0)
    parser.add_argument("--timezone", default="Europe/Moscow")
    parser.add_argument("--sunrise", choices=("hindu", "apparent"), default="hindu")
    parser.add_argument("--output", type=Path, default=Path("brahma_muhurta_2026.csv"))
    args = parser.parse_args()
    if not (-90 <= args.latitude <= 90) or not (-180 <= args.longitude <= 180):
        parser.error("Координаты за допустимыми пределами")
    if args.end < args.start:
        parser.error("Дата --end не может быть раньше --start")
    if (args.end - args.start).days > 3660:
        parser.error("Слишком большой диапазон (более 10 лет)")
    try:
        tz = ZoneInfo(args.timezone)
    except ZoneInfoNotFoundError:
        parser.error("Неизвестная временная зона; установите tzdata")
    rows = []
    current = args.start
    while current <= args.end:
        rows.append(calculate_one(
            current, tz, args.longitude, args.latitude,
            args.elevation, args.sunrise, args.place
        ))
        current += timedelta(days=1)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # UTF-8 BOM для открытия кириллицы в Microsoft Excel на Windows.
    with args.output.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Записано {len(rows)} дат: {args.start} ... {args.end}")
    print(f"Координаты {args.latitude}, {args.longitude}; {tz.key}; {args.sunrise}")
    print("Дата       Восход  Ночь / 15   Фикс. 48 мин")
    for row in (rows[:4] + ([rows[-1]] if len(rows) > 4 else [])):
        print(f"{row['date']} {row['sunrise_local']:>6}  "
              f"{row['brahma_night15_start']}–{row['brahma_night15_end']}   "
              f"{row['brahma_fixed48_start']}–{row['brahma_fixed48_end']}")
    print(f"CSV: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
