import re
from datetime import date, datetime
from decimal import Decimal

import bs4
import httpx

from currency_exchange.enums import Currency
from currency_exchange.exceptions import ExchangeRateUnavailable


class NBPApiService:
    _DATE_REGEX = re.compile(r"\d{4}-\d{2}-\d{2}")
    _RATE_TABLE_ID_REGEX = re.compile(r"a\d{3}z\d{6}")
    _NBP_URL = "https://www.nbp.pl/transfer.aspx?c=/ascx/ListABCH.ascx&Typ=a&p=rok;mies&navid=archa"

    def __init__(self):
        self.client = httpx.AsyncClient()

    @staticmethod
    def table_url(table_id: str) -> str:
        return f"https://www.nbp.pl/kursy/xml/{table_id}.xml"

    async def _get_tables_from_month(self, year: int, month: int) -> dict[date, str]:
        resp = await self.client.get(self._NBP_URL)
        resp.raise_for_status()
        soup = bs4.BeautifulSoup(resp.text, "html.parser")

        inputs = soup.findAll("input")
        data = {input_element["name"]: input_element.get("value", "") for input_element in inputs}
        data["rok"] = str(year % 100).zfill(2)
        data["mies"] = str(month).zfill(2)

        resp = await self.client.post(self._NBP_URL, data=data)
        resp.raise_for_status()
        soup = bs4.BeautifulSoup(resp.text, "html.parser")

        table = soup.find("ul", {"class": "archl"})
        result = {}
        for row in table.find_all("li"):
            rate_date = self._DATE_REGEX.findall(row.text)[0]
            rate_date = datetime.strptime(rate_date, "%Y-%m-%d").date()
            rate_table_id = self._RATE_TABLE_ID_REGEX.findall(row.a["href"])[0]
            result[rate_date] = rate_table_id
        return result

    async def _get_exchange_rate_from_table(self, table_id: str, currency: Currency) -> Decimal:
        resp = await self.client.get(self.table_url(table_id))
        resp.raise_for_status()
        soup = bs4.BeautifulSoup(resp.text, "xml")
        return Decimal(soup.find("kod_waluty", text=currency).parent.find("kurs_sredni").text.replace(",", "."))

    async def get_exchange_rate(self, rate_date: date, currency: Currency) -> Decimal:
        rates_dict = await self._get_tables_from_month(rate_date.year, rate_date.month)
        try:
            rates_table_id = rates_dict[rate_date]
        except KeyError as err:
            raise ExchangeRateUnavailable() from err

        return await self._get_exchange_rate_from_table(rates_table_id, currency)
