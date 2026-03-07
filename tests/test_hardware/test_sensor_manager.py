"""Tests for sensor manager."""


def test_all_limits_initially_false(sensors):
    limits = sensors.get_all_limits()
    # All should be False (not triggered) initially with pull-up
    for name, triggered in limits.items():
        assert triggered is False, f"Limit {name} should not be triggered"


def test_limit_trigger(sensors, sim_backend, pin_map):
    # Simulate pressing limit switch X left (active LOW)
    sim_backend.simulate_press(pin_map.limit_x_left)
    assert sensors.is_limit_triggered("x_left") is True


def test_read_all_sensors(sensors):
    readings = sensors.read_all()
    assert len(readings) == 5  # 5 limit switches
    for reading in readings:
        assert reading.name.startswith("limit_")


def test_sensor_callback(sensors, sim_backend, pin_map):
    events = []
    sensors.on_change(lambda reading: events.append(reading))

    sim_backend.simulate_press(pin_map.limit_z_up)
    assert len(events) == 1
    assert events[0].name == "limit_z_up"
