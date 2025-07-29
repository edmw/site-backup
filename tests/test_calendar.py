from datetime import date, datetime
from unittest.mock import Mock, patch

from backup.archive import Archive
from backup.calendar import Calendar


class TestCalendar:
    """Test cases for Calendar class."""

    def test_calendar_creation_empty(self):
        """Test that Calendar can be created with empty archive list."""
        calendar = Calendar([])
        assert calendar.archives == []
        assert calendar.first_archive is None
        assert calendar.last_archive is None
        assert calendar.today == date.today()
        assert len(calendar.dates) == 0

    def test_calendar_creation_with_custom_today(self):
        """Test that Calendar can be created with custom today date."""
        custom_today = date(2023, 5, 15)
        calendar = Calendar([], today=custom_today)
        assert calendar.today == custom_today

    def test_calendar_creation_with_archives(self):
        """Test that Calendar properly handles archives."""
        archive1 = Mock(spec=Archive)
        archive1.ctime = datetime(2023, 1, 15, 10, 30)
        archive2 = Mock(spec=Archive)
        archive2.ctime = datetime(2023, 3, 20, 14, 45)
        archive3 = Mock(spec=Archive)
        archive3.ctime = datetime(2023, 1, 15, 16, 20)  # Same date as archive1
        archives = [archive2, archive1, archive3]
        calendar = Calendar(archives)  # type: ignore
        assert calendar.archives == [archive1, archive3, archive2]
        assert calendar.first_archive == archive1
        assert calendar.last_archive == archive2
        assert calendar.dates[date(2023, 1, 15)] == 2
        assert calendar.dates[date(2023, 3, 20)] == 1

    def test_formatday_regular_day(self):
        """Test formatday for a regular day without archives."""
        calendar = Calendar([])
        calendar.year = 2023
        calendar.month = 5
        with patch("calendar.HTMLCalendar.formatday") as mock_formatday:
            mock_formatday.return_value = '<td class="mon">15</td>'
            result = calendar.formatday(15, 0)
            assert result == '<td class="mon">15</td>'

    def test_formatday_with_archive(self):
        """Test formatday for a day with archives."""
        archive = Mock(spec=Archive)
        archive.ctime = datetime(2023, 5, 15, 10, 30)
        calendar = Calendar([archive])  # type: ignore
        calendar.year = 2023
        calendar.month = 5
        with patch("calendar.HTMLCalendar.formatday") as mock_formatday:
            mock_formatday.return_value = '<td class="mon">15</td>'
            result = calendar.formatday(15, 0)
            assert '<td class="mon hasarchive">15</td>' == result

    def test_formatday_today(self):
        """Test formatday for today's date."""
        today = date(2023, 5, 15)
        calendar = Calendar([], today=today)
        calendar.year = 2023
        calendar.month = 5
        with patch("calendar.HTMLCalendar.formatday") as mock_formatday:
            mock_formatday.return_value = '<td class="mon">15</td>'
            result = calendar.formatday(15, 0)
            assert '<td class="mon today">15</td>' == result

    def test_formatday_future(self):
        """Test formatday for future dates."""
        today = date(2023, 5, 15)
        calendar = Calendar([], today=today)
        calendar.year = 2023
        calendar.month = 5
        with patch("calendar.HTMLCalendar.formatday") as mock_formatday:
            mock_formatday.return_value = '<td class="tue">16</td>'
            result = calendar.formatday(16, 1)
            assert '<td class="tue future">16</td>' == result

    def test_formatday_with_archive_and_today(self):
        """Test formatday for today's date with archives."""
        today = date(2023, 5, 15)
        archive = Mock(spec=Archive)
        archive.ctime = datetime(2023, 5, 15, 10, 30)
        calendar = Calendar([archive], today=today)  # type: ignore
        calendar.year = 2023
        calendar.month = 5
        with patch("calendar.HTMLCalendar.formatday") as mock_formatday:
            mock_formatday.return_value = '<td class="mon">15</td>'
            result = calendar.formatday(15, 0)
            assert '<td class="mon today hasarchive">15</td>' == result

    def test_formatday_empty_day(self):
        """Test formatday for empty calendar cell (day=0)."""
        calendar = Calendar([])
        with patch("calendar.HTMLCalendar.formatday") as mock_formatday:
            mock_formatday.return_value = '<td class="noday">&nbsp;</td>'
            result = calendar.formatday(0, 0)
            assert result == '<td class="noday">&nbsp;</td>'

    def test_formatmonth(self):
        """Test formatmonth sets year and month attributes."""
        calendar = Calendar([])
        with patch("calendar.HTMLCalendar.formatmonth") as mock_formatmonth:
            mock_formatmonth.return_value = "<table>...</table>"
            result = calendar.formatmonth(2023, 5, withyear=True)
            assert calendar.year == 2023
            assert calendar.month == 5
            assert result == "<table>...</table>"
            mock_formatmonth.assert_called_once_with(2023, 5, withyear=True)

    def test_formatpage(self):
        """Test formatpage creates proper HTML structure."""
        calendar = Calendar([])
        content = "<table>Test content</table>"
        result = calendar.formatpage(content)
        assert "<!DOCTYPE HTML>" in result
        assert "<html>" in result
        assert "<head>" in result
        assert '<meta charset="utf-8">' in result
        assert "<title>Calendar</title>" in result
        assert '<style type="text/css">' in result
        assert calendar.CSS in result
        assert "</style>" in result
        assert "</head>" in result
        assert "<body>" in result
        assert content in result
        assert "</body>" in result
        assert "</html>" in result

    def test_css_contains_required_styles(self):
        """Test that CSS contains required style classes."""
        calendar = Calendar([])
        css = calendar.CSS
        assert ".today" in css
        assert ".future" in css
        assert ".hasarchive" in css
        assert "table.year" in css
        assert "table.month" in css
        assert "th.year" in css
        assert "th.month" in css

    def test_format_empty_archives(self):
        """Test format method with no archives."""
        today = date(2023, 5, 15)
        calendar = Calendar([], today=today)
        with patch.object(calendar, "formatyear") as mock_formatyear:
            with patch.object(calendar, "formatpage") as mock_formatpage:
                mock_formatpage.return_value = "formatted_page"
                result = calendar.format()
                mock_formatyear.assert_not_called()
                mock_formatpage.assert_called_once_with("")
                assert result == "formatted_page"

    def test_format_single_year(self):
        """Test format method with archives in single year."""
        archive1 = Mock(spec=Archive)
        archive1.ctime = datetime(2023, 1, 15, 10, 30)
        archive2 = Mock(spec=Archive)
        archive2.ctime = datetime(2023, 3, 20, 14, 45)
        today = date(2023, 5, 15)
        calendar = Calendar([archive1, archive2], today=today)  # type: ignore
        with patch.object(calendar, "formatyear") as mock_formatyear:
            with patch.object(calendar, "formatpage") as mock_formatpage:
                mock_formatyear.return_value = "<year_content>"
                mock_formatpage.return_value = "formatted_page"
                result = calendar.format()
                mock_formatyear.assert_called_once_with(2023)
                mock_formatpage.assert_called_once_with("<year_content>")
                assert result == "formatted_page"

    def test_format_multiple_years(self):
        """Test format method with archives spanning multiple years."""
        archive1 = Mock(spec=Archive)
        archive1.ctime = datetime(2022, 12, 15, 10, 30)
        archive2 = Mock(spec=Archive)
        archive2.ctime = datetime(2023, 3, 20, 14, 45)
        archive3 = Mock(spec=Archive)
        archive3.ctime = datetime(2024, 1, 10, 9, 15)
        today = date(2023, 5, 15)
        calendar = Calendar([archive1, archive2, archive3], today=today)  # type: ignore
        with patch.object(calendar, "formatyear") as mock_formatyear:
            with patch.object(calendar, "formatpage") as mock_formatpage:
                mock_formatyear.side_effect = ["<year2022>", "<year2023>", "<year2024>"]
                mock_formatpage.return_value = "formatted_page"
                result = calendar.format()
                assert mock_formatyear.call_count == 3
                mock_formatyear.assert_any_call(2022)
                mock_formatyear.assert_any_call(2023)
                mock_formatyear.assert_any_call(2024)
                mock_formatpage.assert_called_once_with(
                    "<year2022><year2023><year2024>"
                )
                assert result == "formatted_page"

    def test_format_year_without_archives_skipped(self):
        """Test format method skips years without archives."""
        archive1 = Mock(spec=Archive)
        archive1.ctime = datetime(2022, 12, 15, 10, 30)
        archive2 = Mock(spec=Archive)
        archive2.ctime = datetime(2024, 3, 20, 14, 45)
        today = date(2023, 5, 15)
        calendar = Calendar([archive1, archive2], today=today)  # type: ignore
        with patch.object(calendar, "formatyear") as mock_formatyear:
            with patch.object(calendar, "formatpage") as mock_formatpage:
                mock_formatyear.side_effect = ["<year2022>", "<year2024>"]
                mock_formatpage.return_value = "formatted_page"
                result = calendar.format()
                assert mock_formatyear.call_count == 2
                mock_formatyear.assert_any_call(2022)
                mock_formatyear.assert_any_call(2024)
                mock_formatpage.assert_called_once_with("<year2022><year2024>")
                assert result == "formatted_page"

    def test_format_uses_today_year_when_no_archives(self):
        """Test format method uses today's year when no archives exist."""
        today = date(2023, 5, 15)
        calendar = Calendar([], today=today)
        assert calendar.first_archive is None
        assert calendar.last_archive is None
        with patch.object(calendar, "formatyear") as mock_formatyear:
            with patch.object(calendar, "formatpage") as mock_formatpage:
                mock_formatpage.return_value = "formatted_page"
                _ = calendar.format()
                mock_formatyear.assert_not_called()
                mock_formatpage.assert_called_once_with("")


class TestCalendarIntegration:
    """Integration tests for Calendar class with real Archive objects."""

    def test_calendar_with_real_archive_structure(self):
        """Test calendar with archive-like objects that have proper ctime attributes."""

        class MockArchive:
            def __init__(self, year, month, day, hour=10, minute=0):
                self.ctime = datetime(year, month, day, hour, minute)

        archives = [
            MockArchive(2023, 1, 15),
            MockArchive(2023, 1, 15, 14, 30),
            MockArchive(2023, 2, 28),
            MockArchive(2023, 12, 25),
            MockArchive(2024, 1, 1),
        ]
        today = date(2023, 6, 15)
        calendar = Calendar(archives, today=today)  # type: ignore
        assert len(calendar.archives) == 5
        assert calendar.first_archive is not None
        assert calendar.first_archive.ctime.year == 2023
        assert calendar.first_archive.ctime.month == 1
        assert calendar.last_archive is not None
        assert calendar.last_archive.ctime.year == 2024
        assert calendar.dates[date(2023, 1, 15)] == 2
        assert calendar.dates[date(2023, 2, 28)] == 1
        assert calendar.dates[date(2023, 12, 25)] == 1
        assert calendar.dates[date(2024, 1, 1)] == 1
        assert calendar.first_archive is not None
        assert calendar.last_archive is not None
        assert calendar.first_archive.ctime.year == 2023
        assert calendar.last_archive.ctime.year == 2024

    def test_calendar_html_output_structure(self):
        """Test that the HTML output has proper structure."""

        class MockArchive:
            def __init__(self, year, month, day):
                self.ctime = datetime(year, month, day, 10, 0)

        archives = [MockArchive(2023, 5, 15)]
        today = date(2023, 5, 16)
        calendar = Calendar(archives, today=today)  # type: ignore
        html_output = calendar.format()
        assert html_output.startswith("<!DOCTYPE HTML>")
        assert "<html>" in html_output
        assert "<title>Calendar</title>" in html_output
        assert '<style type="text/css">' in html_output
        assert calendar.CSS in html_output
        assert html_output.endswith("</html>")
