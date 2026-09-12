from app.services.metrics import compute_funnel


def test_counts_known_statuses_into_buckets():
    statuses = ["New", "New", "Assigned", "Appointment Booked", "Dead"]
    result = compute_funnel(statuses)
    assert result["new"] == 2
    assert result["contacted"] == 1
    assert result["appointment_booked"] == 1
    assert result["dead"] == 1
    assert result["total"] == 5


def test_unknown_status_falls_into_other():
    result = compute_funnel(["Some Unmapped Status"])
    assert result["other"] == 1
    assert result["total"] == 1


def test_empty_list():
    result = compute_funnel([])
    assert result["total"] == 0
    assert all(v == 0 for k, v in result.items() if k != "total")
