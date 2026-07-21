"""Smoke tests — require ClickHouse to be running."""
import sys
sys.path.insert(0, ".")

import pytest
from config import get_client
from queries.executive import (
    kpi_summary, identity_funnel, tier_mix, revenue_by_type,
    monthly_revenue, top_destinations, top_customers, city_revenue_for_map,
)
from queries.customer import search, total_count
from queries.customer_360 import fetch as fetch_360
from queries.routes import route_table, monthly_trend, holiday_comparison, business_class_share

@pytest.fixture(scope="module")
def ch():
    return get_client()


class TestExecutive:
    def test_kpi_summary(self, ch):
        kpi = kpi_summary(ch)
        assert kpi["total_customers"] > 0
        assert kpi["total_revenue"] >= 0

    def test_identity_funnel(self, ch):
        df = identity_funnel(ch)
        assert len(df) >= 1

    def test_tier_mix(self, ch):
        df = tier_mix(ch)
        assert len(df) == 3
        assert "loyalty_tier" in df.columns

    def test_revenue_by_type(self, ch):
        df = revenue_by_type(ch)
        assert len(df) >= 1

    def test_monthly_revenue(self, ch):
        df = monthly_revenue(ch)
        assert len(df) > 0

    def test_top_destinations(self, ch):
        df = top_destinations(ch, limit=5)
        assert len(df) <= 5

    def test_top_customers(self, ch):
        df = top_customers(ch, limit=5)
        assert len(df) <= 5

    def test_city_revenue_for_map(self, ch):
        df = city_revenue_for_map(ch)
        assert len(df) > 0


class TestCustomerExplorer:
    def test_search(self, ch):
        df = search(ch, limit=10)
        assert len(df) > 0
        assert "resolved_customer_id" in df.columns

    def test_search_with_filters(self, ch):
        df = search(ch, tiers=["gold"], limit=10)
        assert len(df) >= 0  # may be zero if no gold customers

    def test_search_omnichannel(self, ch):
        df = search(ch, omnichannel=True, limit=10)
        assert len(df) >= 0

    def test_total_count(self, ch):
        cnt = total_count(ch)
        assert cnt > 0


class TestCustomer360:
    def test_fetch_valid_customer(self, ch):
        df = search(ch, limit=1, tiers=[])
        assert len(df) > 0
        rcid = df.iloc[0]["resolved_customer_id"]
        data = fetch_360(ch, rcid)
        assert data["customer"] is not None
        assert data["bookings"] is not None

    def test_fetch_invalid(self, ch):
        data = fetch_360(ch, "nonexistent_rcid")
        assert data["customer"] is None


class TestRoutes:
    def test_route_table(self, ch):
        df = route_table(ch, limit=10)
        assert len(df) >= 1

    def test_monthly_trend(self, ch):
        df = monthly_trend(ch)
        assert len(df) > 0

    def test_holiday_comparison(self, ch):
        df = holiday_comparison(ch)
        assert len(df) >= 0

    def test_business_class_share(self, ch):
        df = business_class_share(ch)
        assert len(df) >= 0
