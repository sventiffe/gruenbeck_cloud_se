"""Entity descriptions, shown as attribute in the language of Home Assistant.

Home Assistant has no tooltips for entities, so each entity exposes a short
explanation as "description" attribute.
"""
from __future__ import annotations

DESCRIPTIONS: dict[str, dict[str, str]] = {
    "mrescapa1": {
        "en": "Soft water the exchanger can still deliver until the next regeneration.",
        "de": "Weichwassermenge, die der Austauscher bis zur nächsten Regeneration noch liefern kann.",
    },
    "mresidcap1": {
        "en": "Remaining capacity of the exchanger in percent. 100 % right after a regeneration.",
        "de": "Restkapazität des Austauschers in Prozent. Direkt nach einer Regeneration 100 %.",
    },
    "mcapacity": {
        "en": "Nominal capacity of the device (m³ × °dH) the softener uses to plan regenerations.",
        "de": "Nennkapazität der Anlage (m³ × °dH), mit der die Anlage die Regenerationen plant.",
    },
    "mcountreg": {
        "en": "Number of regenerations since start-up.",
        "de": "Anzahl der Regenerationen seit der Inbetriebnahme.",
    },
    "msaltusage": {
        "en": "Total salt usage as reported by the device. Stays at 0 on some SE models, use the sum of daily values instead.",
        "de": "Gesamter Salzverbrauch laut Anlage. Bleibt bei manchen SE-Modellen auf 0, dann die Summe der Tageswerte verwenden.",
    },
    "mflow1": {
        "en": "Current soft water flow. Only up to date in live mode or while a poll happens during water usage.",
        "de": "Aktueller Weichwasser-Durchfluss. Nur aktuell im Live-Modus oder wenn eine Abfrage gerade während der Wasserentnahme stattfindet.",
    },
    "mcurrent": {
        "en": "Current of the chlorine cell that disinfects the resin during regeneration. Only non-zero while it is active.",
        "de": "Strom der Chlorzelle, die das Harz während der Regeneration desinfiziert. Nur während sie arbeitet ungleich 0.",
    },
    "mregstatus": {
        "en": "Raw regeneration status code of the device (0 = no regeneration).",
        "de": "Roher Regenerationsstatus der Anlage (0 = keine Regeneration).",
    },
    "mcountwater1": {
        "en": "Soft water meter of the device in whole m³ (\"water volume 0 °dH\" in the app).",
        "de": "Weichwasserzähler der Anlage in ganzen m³ (in der App \"Wassermenge 0 °dH\").",
    },
    "mcountwater2": {
        "en": "Second soft water meter of the device in whole m³.",
        "de": "Zweiter Weichwasserzähler der Anlage in ganzen m³.",
    },
    "mcountwatertank": {
        "en": "Water the device used to refill the brine tank, in liters (\"make-up volume\" in the app).",
        "de": "Wasser, mit dem die Anlage den Solebehälter nachgespeist hat, in Litern (in der App \"Nachspeisemenge\").",
    },
    "mmaint": {
        "en": "Days until the next maintenance is due.",
        "de": "Tage bis zur nächsten fälligen Wartung.",
    },
    "mhardsoftw": {
        "en": "Measured hardness of the soft water.",
        "de": "Gemessene Härte des Weichwassers.",
    },
    "mlifeadsorb": {
        "en": "How far the adsorber is exhausted.",
        "de": "Wie weit der Adsorber erschöpft ist.",
    },
    "mflowmax": {
        "en": "Highest flow rate the device has measured.",
        "de": "Höchster Durchfluss, den die Anlage gemessen hat.",
    },
    "mendreg1": {
        "en": "Time of day when the last regeneration ended.",
        "de": "Uhrzeit, zu der die letzte Regeneration endete.",
    },
    "mendreg2": {
        "en": "Time of day when the last regeneration of the second exchanger ended.",
        "de": "Uhrzeit, zu der die letzte Regeneration des zweiten Austauschers endete.",
    },
    "mregpercent1": {
        "en": "Progress of the running regeneration.",
        "de": "Fortschritt der laufenden Regeneration.",
    },
    "mremregstep": {
        "en": "Remaining amount or time of the current regeneration step (raw value).",
        "de": "Restmenge bzw. Restzeit des aktuellen Regenerationsschritts (Rohwert).",
    },
    "regeneration_phase": {
        "en": "Current regeneration phase in plain text. The mapping comes from other Grünbeck models; unknown values show as 'Other' with the raw value as attribute.",
        "de": "Aktuelle Regenerationsphase im Klartext. Die Zuordnung stammt von anderen Grünbeck-Modellen; unbekannte Werte erscheinen als 'Sonstige' mit dem Rohwert als Attribut.",
    },
    "next_regeneration_window": {
        "en": "Next of the configured regeneration times. In IQ mode the device decides itself whether it regenerates then, depending on the remaining capacity.",
        "de": "Nächste der eingestellten Regenerationszeiten. Im IQ-Modus entscheidet die Anlage je nach Restkapazität selbst, ob sie dann regeneriert.",
    },
    "last_regeneration": {
        "en": "When the last regeneration was detected (the regeneration counter increased). Accurate to the polling interval; unknown until the first regeneration after installing this version. The history attribute lists the last 20 regenerations with the remaining capacity before them.",
        "de": "Wann die letzte Regeneration erkannt wurde (der Regenerationszähler ist gestiegen). Genau auf das Abfrageintervall; bis zur ersten Regeneration nach dem Update unbekannt. Das Attribut Verlauf enthält die letzten 20 Regenerationen mit der Restkapazität davor.",
    },
    "startup": {
        "en": "Date the device was put into operation.",
        "de": "Datum der Inbetriebnahme der Anlage.",
    },
    "software_version": {
        "en": "Firmware version of the device control.",
        "de": "Firmware-Version der Steuerung.",
    },
    "last_error": {
        "en": "Newest unresolved error message from the cloud, 'OK' if there is none. All errors are listed in the attribute.",
        "de": "Neueste offene Fehlermeldung aus der Cloud, 'OK' wenn keine vorliegt. Alle Fehler stehen im Attribut.",
    },
    "raw_water_hardness": {
        "en": "Hardness of the incoming tap water as configured in the device.",
        "de": "Härte des zulaufenden Leitungswassers, so wie in der Anlage eingestellt.",
    },
    "soft_water_hardness": {
        "en": "Target hardness after the softener. The device blends raw water to reach it.",
        "de": "Zielhärte nach der Anlage. Die Anlage mischt dafür Rohwasser bei.",
    },
    "regeneration_time": {
        "en": "Configured regeneration times. In IQ mode the device may choose other times.",
        "de": "Eingestellte Regenerationszeiten. Im IQ-Modus kann die Anlage davon abweichen.",
    },
    "maintenance_interval": {
        "en": "Configured interval between two maintenances.",
        "de": "Eingestellter Abstand zwischen zwei Wartungen.",
    },
    "nominal_flow": {
        "en": "Nominal flow rate of the device.",
        "de": "Nenndurchfluss der Anlage.",
    },
    "water_yesterday": {
        "en": "Water usage of yesterday according to the cloud. The cloud only provides completed days; the attribute lists the last days.",
        "de": "Wasserverbrauch von gestern laut Cloud. Die Cloud liefert nur abgeschlossene Tage; das Attribut enthält die letzten Tage.",
    },
    "lime_retained_yesterday": {
        "en": "Lime the softener removed from the water yesterday, according to the cloud.",
        "de": "Kalk, den die Anlage gestern aus dem Wasser entfernt hat, laut Cloud.",
    },
    "salt_yesterday": {
        "en": "Salt used yesterday according to the cloud. 0 on days without regeneration.",
        "de": "Salzverbrauch von gestern laut Cloud. An Tagen ohne Regeneration 0.",
    },
    "salt_daily_sum": {
        "en": "Sum of all daily salt values the cloud returns. Covers only the days listed in the attributes.",
        "de": "Summe aller Tageswerte für Salz, die die Cloud liefert. Umfasst nur die in den Attributen genannten Tage.",
    },
    "calculated_water_consumption": {
        "en": "Running total of soft water, calculated from the decreasing remaining capacity. Suitable for the energy dashboard. Does not include blended raw water.",
        "de": "Fortlaufender Weichwasserverbrauch, berechnet aus der sinkenden Restkapazität. Geeignet für das Energie-Dashboard. Ohne beigemischtes Rohwasser.",
    },
    "average_flow_rate": {
        "en": "Average soft water flow between the last two polls. Shows an average, not peaks.",
        "de": "Mittlerer Weichwasser-Durchfluss zwischen den letzten beiden Abfragen. Zeigt einen Mittelwert, keine Spitzen.",
    },
    "data_last_changed": {
        "en": "When the device data last changed. If it stays the same for hours while water is used, the cloud data is frozen (device error or rate limiting).",
        "de": "Wann sich die Gerätedaten zuletzt geändert haben. Bleibt der Wert stundenlang gleich, obwohl Wasser läuft, ist die Cloud eingefroren (Gerätefehler oder Abfragebegrenzung).",
    },
    "has_error": {
        "en": "On if the device reports an error. While an error is pending, the device stops sending new data.",
        "de": "An, wenn die Anlage einen Fehler meldet. Solange ein Fehler ansteht, sendet die Anlage keine neuen Daten.",
    },
    "salt_warning": {
        "en": "On if the salt supply needs attention.",
        "de": "An, wenn der Salzvorrat Aufmerksamkeit braucht.",
    },
    "regeneration_running": {
        "en": "On while a regeneration is running. Only as accurate as the polling interval.",
        "de": "An, solange eine Regeneration läuft. Nur so genau wie das Abfrageintervall.",
    },
    "iq_mode": {
        "en": "iQ-Mode: the device decides itself when to regenerate, based on the learned water usage. Off = regeneration at the fixed times only.",
        "de": "iQ-Mode: Die Anlage entscheidet anhand des gelernten Wasserverbrauchs selbst, wann sie regeneriert. Aus = Regeneration nur zu den festen Zeitpunkten.",
    },
    "led_brightness": {
        "en": "Brightness of the illuminated ring on the device. Changes take a moment to reach the device.",
        "de": "Helligkeit des Leuchtrings an der Anlage. Änderungen brauchen einen Moment, bis sie an der Anlage ankommen.",
    },
    "live_mode": {
        "en": "Polls every 30 seconds for 5 minutes, then switches off by itself. For a quick look at the current flow.",
        "de": "Fragt 5 Minuten lang alle 30 Sekunden ab und schaltet sich dann selbst aus. Für einen schnellen Blick auf den aktuellen Durchfluss.",
    },
    "track_regeneration": {
        "en": "When a running regeneration is detected, polls every minute until it ends (max. 60 minutes), then returns to the normal interval.",
        "de": "Erkennt eine laufende Regeneration und fragt dann bis zu deren Ende jede Minute ab (höchstens 60 Minuten), danach wieder im normalen Takt.",
    },
}

DESCRIPTIONS.update({
    "mrescapa2": {
        "en": "Soft water the second exchanger can still deliver. Only on devices with two exchangers.",
        "de": "Weichwassermenge, die der zweite Austauscher noch liefern kann. Nur bei Anlagen mit zwei Austauschern.",
    },
    "mresidcap2": {
        "en": "Remaining capacity of the second exchanger in percent. Only on devices with two exchangers.",
        "de": "Restkapazität des zweiten Austauschers in Prozent. Nur bei Anlagen mit zwei Austauschern.",
    },
    "mflow2": {
        "en": "Current flow through the second exchanger. Only up to date in live mode.",
        "de": "Aktueller Durchfluss durch den zweiten Austauscher. Nur im Live-Modus aktuell.",
    },
    "mflowblend": {
        "en": "Current flow through the blending valve. Only up to date in live mode.",
        "de": "Aktueller Durchfluss durch das Verschneideventil. Nur im Live-Modus aktuell.",
    },
    "buzzer": {
        "en": "Acoustic signal of the device on errors (\"signal on failure\" in the app). Changes take effect once the device has picked them up.",
        "de": "Akustisches Signal der Anlage bei Störungen (in der App \"Signal bei Störung\"). Wirkt, sobald die Anlage die Änderung übernommen hat.",
    },
    "led_ring_permanent": {
        "en": "LED ring lights up permanently. Switches the other LED ring options off, as in the app.",
        "de": "LED-Ring leuchtet dauerhaft. Schaltet wie in der App die anderen LED-Ring-Optionen aus.",
    },
    "led_ring_failure": {
        "en": "LED ring lights up on failures. Switching it off also switches off \"on message\" and \"on flow\".",
        "de": "LED-Ring leuchtet bei Störungen. Ausschalten schaltet auch \"bei Meldung\" und \"bei Durchfluss\" aus.",
    },
    "led_ring_message": {
        "en": "LED ring lights up on messages. The device stores this together with \"on failure\", so that is switched on as well.",
        "de": "LED-Ring leuchtet bei Meldungen. Die Anlage speichert das nur zusammen mit \"bei Störung\", das wird also mit eingeschaltet.",
    },
    "led_ring_flow": {
        "en": "LED ring lights up while water flows. Also switches on \"on message\" and \"on failure\".",
        "de": "LED-Ring leuchtet bei Durchfluss. Schaltet auch \"bei Meldung\" und \"bei Störung\" mit ein.",
    },
    "last_poll": {
        "en": "Time of the last successful poll of the live data, normally every polling interval (10 minutes by default). Unlike \"Data last changed\", it also moves when no value has changed.",
        "de": "Zeitpunkt der letzten erfolgreichen Abfrage der Live-Daten, normalerweise im eingestellten Abfrageintervall (Standard 10 Minuten). Anders als \"Daten zuletzt geändert\" läuft er auch weiter, wenn sich kein Wert geändert hat.",
    },
    "setting_changes": {
        "en": "Time of the last changed setting in the cloud. The attribute lists the last changes (parameter: old → new). Settings are read hourly or with the button \"Fetch settings now\".",
        "de": "Zeitpunkt der letzten geänderten Einstellung in der Cloud. Das Attribut listet die letzten Änderungen (Parameter: alt → neu). Einstellungen werden stündlich gelesen oder mit dem Button \"Einstellungen jetzt abrufen\".",
    },
    "refresh_settings": {
        "en": "Reads device info and settings from the cloud now. Does not wake the device, so it does not count against the rate limit.",
        "de": "Liest Geräteinfos und Einstellungen sofort aus der Cloud. Weckt die Anlage nicht und zählt daher nicht zur Abfragebegrenzung.",
    },
    "last_maintenance": {
        "en": "Date of the last maintenance. Stored in Home Assistant because the cloud does not know it. Defaults to the start-up date; can be set freely, also retroactively.",
        "de": "Datum der letzten Wartung. Wird in Home Assistant gespeichert, weil die Cloud es nicht kennt. Startwert ist die Inbetriebnahme; frei einstellbar, auch rückwirkend.",
    },
    "last_inspection": {
        "en": "Date of the last inspection. Stored in Home Assistant. Defaults to the start-up date; can be set freely.",
        "de": "Datum der letzten Inspektion. Wird in Home Assistant gespeichert. Startwert ist die Inbetriebnahme; frei einstellbar.",
    },
    "maintenance_done": {
        "en": "Sets the date of the last maintenance to today.",
        "de": "Setzt das Datum der letzten Wartung auf heute.",
    },
    "inspection_done": {
        "en": "Sets the date of the last inspection to today.",
        "de": "Setzt das Datum der letzten Inspektion auf heute.",
    },
    "next_maintenance": {
        "en": "Last maintenance plus the maintenance interval configured in the device.",
        "de": "Letzte Wartung plus das in der Anlage eingestellte Wartungsintervall.",
    },
    "next_inspection": {
        "en": "Last inspection plus the inspection interval configured in the device.",
        "de": "Letzte Inspektion plus das in der Anlage eingestellte Inspektionsintervall.",
    },
    "maintenance_days_remaining": {
        "en": "Days until the next maintenance. Negative when overdue.",
        "de": "Tage bis zur nächsten Wartung. Negativ, wenn überfällig.",
    },
    "inspection_days_remaining": {
        "en": "Days until the next inspection. Negative when overdue.",
        "de": "Tage bis zur nächsten Inspektion. Negativ, wenn überfällig.",
    },
})

# Names of the attributes, used for the state_attributes translations
ATTRIBUTE_NAMES: dict[str, dict[str, str]] = {
    "description": {"en": "Description", "de": "Beschreibung"},
    "daily": {"en": "Daily values", "de": "Tageswerte"},
    "errors": {"en": "Errors", "de": "Fehler"},
    "consumed_liters": {"en": "Consumed since last poll (L)", "de": "Verbrauch seit letzter Abfrage (L)"},
    "raw_value": {"en": "Raw value", "de": "Rohwert"},
    "days": {"en": "Days", "de": "Tage"},
    "first_day": {"en": "First day", "de": "Erster Tag"},
    "regeneration_count": {"en": "Regeneration count", "de": "Regenerationszähler"},
    "history": {"en": "History", "de": "Verlauf"},
    "changes": {"en": "Changes", "de": "Änderungen"},
}


def get_description(key: str, language: str) -> str | None:
    """Return the description in the given language, English as fallback."""
    texts = DESCRIPTIONS.get(key)
    if texts is None:
        return None
    return texts.get(language.split("-")[0], texts["en"])
