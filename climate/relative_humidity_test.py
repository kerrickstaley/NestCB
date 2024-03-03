from climate.relative_humidity import relative_humidity


def test_relative_humidity():
    assert round(relative_humidity(-22.4, -25.5), 2) == 75.83
