def test_dele_b1_information_page_renders(client):
    res = client.get("/info/dele-b1")
    assert res.status_code == 200

    html = res.get_data(as_text=True)
    assert "DELE B1 Information" in html
    assert "Volver al menú principal" in html
    assert "Tiempos y modos verbales" in html
    assert "nivel umbral" in html
    # At least one inline hover explanation (title attribute) should be present
    assert 'title="DE: Schwellenstufe | EN: threshold level"' in html


def test_main_menu_links_to_dele_b1_information(client):
    res = client.get("/")
    assert res.status_code == 200

    html = res.get_data(as_text=True)
    assert "/info/dele-b1" in html

