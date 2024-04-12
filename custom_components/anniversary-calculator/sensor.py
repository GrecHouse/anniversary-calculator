"""
Anniversary sensor supporting the lunar calendar.
For more details about this platform, please refer to the documentation at
https://github.com/GrecHouse/anniversary_calculator

HA 기념일 센서 : 기념일의 D-Day 정보와 양/음력 정보를 알려줍니다.
다모아님의 아이디어를 기반으로 제작되었습니다.
"""

from datetime import timedelta, date, datetime
import logging

import voluptuous as vol

from homeassistant.core import callback
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_point_in_utc_time
import homeassistant.helpers.config_validation as cv
import homeassistant.util.dt as dt_util

from korean_lunar_calendar import KoreanLunarCalendar

from .const import *

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """통합 구성요소의 sensor 플랫폼 Entry 설정"""

    _LOGGER.debug(entry.data)

    date_str = entry.data.get(CONF_DATE)
    is_lunar = entry.data.get(CONF_LUNAR)
    is_intercalation = entry.data.get(CONF_INTERCAL)
    anniv_type = entry.data.get(CONF_TYPE)
    name = entry.data.get(CONF_NAME)

    is_mmdd = False
    if dt_util.parse_date(date_str) is None:
        year_added_date_str = str(dt_util.as_local(dt_util.utcnow()).date().year) + "-" + date_str
        if dt_util.parse_date(year_added_date_str) is not None:
            date_str = year_added_date_str
            is_mmdd = True

    sensor = AnniversarySensor(hass, name, date_str, is_lunar, is_intercalation, anniv_type, is_mmdd)
    async_track_point_in_utc_time(hass, sensor.point_in_time_listener, sensor.get_next_interval())

    async_add_entities([sensor])

class AnniversarySensor(Entity):
    """Implementation of a Anniversary sensor."""

    def __init__(self, hass, name, date_str, lunar, intercalation, anniv_type, mmdd):
        """Initialize the sensor."""
        #self.entity_id = async_generate_entity_id(ENTITY_ID_FORMAT, deviceId, hass=hass)
        self._name = name
        self._date = dt_util.parse_date(date_str)
        self._lunar = lunar
        self._intercalation = intercalation
        self._type = anniv_type
        self._mmdd = mmdd
        self._state = None
        self.hass = hass
        self._update_internal_state(dt_util.utcnow())
        self.firmware_version = SW_VERSION
        self.model = MODEL
        self.manufacturer = MANUFACT

    @property
    def device_info(self):
        """Information about this entity/device."""
        return {
            "identifiers": {(DOMAIN, self._name)},
            "name": self._name,
            "sw_version": self.firmware_version,
            "model": self.model,
            "manufacturer": self.manufacturer
        }

    @property
    def attribution(self):
        """Return the attribution."""
        return ATTRIBUTION

    @property
    def unique_id(self):
        """Return the entity ID."""
        return f'sensor.anniv_{self._name}'

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        if self._type == 'birth':
            return 'mdi:calendar-star'
        elif self._type == 'wedding':
            return 'mdi:calendar-heart'
        elif self._type == 'memorial':
            return 'mdi:calendar-clock'
        else:
            return 'mdi:calendar-check'

    @property
    def extra_state_attributes(self):
        """Return the attribute(s) of the sensor"""
        return self._attribute

    def solar_to_lunar(self, solar_date):
        calendar = KoreanLunarCalendar()
        calendar.setSolarDate(solar_date.year, solar_date.month, solar_date.day)
        lunar = calendar.LunarIsoFormat()
        lunar = lunar.replace(' Intercalation', INTERCALATION)
        return lunar

    def lunar_to_solar(self, today, this_year):
        lunar_date = self._date
        calendar = KoreanLunarCalendar()
        if this_year or self._mmdd:
            calendar.setLunarDate(today.year, lunar_date.month, lunar_date.day, self._intercalation)
            if calendar.SolarIsoFormat() == '0000-00-00':
                lunar_date_calib = lunar_date - timedelta(1)
                calendar.setLunarDate(today.year, lunar_date_calib.month, lunar_date_calib.day, self._intercalation)
                _LOGGER.warning("Non-existent date correction : %s -> %s", lunar_date, calendar.SolarIsoFormat())
        else:
            calendar.setLunarDate(lunar_date.year, lunar_date.month, lunar_date.day, self._intercalation)
        return dt_util.parse_date(calendar.SolarIsoFormat())

    def lunar_to_solar_early_day(self, today):
        lunar_date = self._date
        calendar = KoreanLunarCalendar()
        calendar.setLunarDate(today.year-1, lunar_date.month, lunar_date.day, self._intercalation)
        if calendar.SolarIsoFormat() == '0000-00-00':
            lunar_date_calib = lunar_date - timedelta(1)
            calendar.setLunarDate(today.year-1, lunar_date_calib.month, lunar_date_calib.day, self._intercalation)
            _LOGGER.warning("Non-existent date correction : %s -> %s", lunar_date, calendar.SolarIsoFormat())
        return dt_util.parse_date(calendar.SolarIsoFormat())

    def lunar_gapja(self, lunarDate):
        intercalation = False
        if '윤달' in lunarDate:
            intercalation = True
            lunarDate = lunarDate.replace(INTERCALATION,'')
        calendar = KoreanLunarCalendar()
        try:
            lunar = dt_util.parse_date(lunarDate)
            calendar.setLunarDate(lunar.year, lunar.month, lunar.day, intercalation)
        except AttributeError:
            try:
                calendar.setLunarDate(lunarDate[:4], lunarDate[5:7], lunarDate[8:], intercalation)
            except:
                return "-"
        return calendar.getGapJaString()

    def is_past(self, today):
        anniv = self._date
        if self._lunar:
            anniv = self.lunar_to_solar(today, True)
        else:
            anniv = date(today.year, anniv.month, anniv.day)
        if (anniv-today).days < 0:
            return True
        else:
            return False

    def past_days(self, today):
        anniv = self._date
        if self._lunar:
            anniv = self.lunar_to_solar(today, False)
        delta = today - anniv
        return delta.days + 1

    def korean_age(self, today, dday):
        addyear = 1 + dt_util.parse_date(dday).year - today.year
        return today.year - self._date.year + addyear

    def upcoming_count(self, today):
        anniv = self._date
        if self._lunar:
            anniv = self.lunar_to_solar(today, False)

        if self.is_past(today):
            return today.year - anniv.year + 1
        else:
            return today.year - anniv.year

    def d_day(self, today):
        anniv = self._date

        if self._lunar:
            anniv_early_day = self.lunar_to_solar_early_day(today)
            delta = anniv_early_day - today
            if delta.days >= 0:
                return [delta.days, anniv_early_day.strftime('%Y-%m-%d')]

        if self.is_past(today):
            if self._lunar:
                if today.month == 2 and today.day == 29:
                    newday = date(today.year+1, today.month, today.day-1)
                else:
                    newday = date(today.year+1, today.month, today.day)
                anniv = self.lunar_to_solar(newday, True)
            else:
                if anniv.month == 2 and anniv.day == 29:
                    anniv = date(today.year+1, anniv.month, anniv.day-1)
                else:
                    anniv = date(today.year+1, anniv.month, anniv.day)
        else:
            if self._lunar:
                anniv = self.lunar_to_solar(today, True)
            else:
                anniv = date(today.year, anniv.month, anniv.day)

        delta = anniv - today
        return [delta.days, anniv.strftime('%Y-%m-%d')]

    def get_next_interval(self, now=None):
        """Compute next time an update should occur."""
        if now is None:
            now = dt_util.utcnow()
        midnight = dt_util.start_of_local_day(dt_util.as_local(now))
        return midnight + timedelta(seconds=86400)

    def _update_internal_state(self, time_date):
        today = dt_util.as_local(dt_util.utcnow()).date()
        dday = self.d_day(today)
        self._state = dday[0]
        solar_date = self._date
        lunar_date = self._date.strftime('%Y-%m-%d')
        if self._intercalation:
            lunar_date = lunar_date + INTERCALATION
        if self._lunar:
            solar_date = self.lunar_to_solar(today, False)
        else:
            lunar_date = self.solar_to_lunar(self._date)

        self._attribute = {
            'type': self._type,
            'solar_date': solar_date.strftime('%Y-%m-%d'),
            'lunar_date': lunar_date,
            'lunar_date_gapja': self.lunar_gapja(lunar_date),
            'past_days': '-' if self._mmdd else self.past_days(today),
            'upcoming_count': '-' if self._mmdd else self.upcoming_count(today),
            'upcoming_date': dday[1],
            'korean_age': '-' if self._mmdd or self._type != 'birth' else self.korean_age(today, dday[1]),
            'is_lunar': str(self._lunar),
            'is_mmdd': str(self._mmdd)
        }

    @callback
    def point_in_time_listener(self, time_date):
        """Get the latest data and update state."""
        self._update_internal_state(time_date)
        self.async_schedule_update_ha_state()
        async_track_point_in_utc_time(self.hass, self.point_in_time_listener, self.get_next_interval())
