def test_full_presentation_lifecycle_across_http_boundary(client):
    """Test crossing real HTTP boundary for complete presentation lifecycle."""
    # 1. Obtain demo analyst token
    auth_resp = client.post("/api/auth/demo-login", json={"role": "analyst"})
    assert auth_resp.status_code == 200
    token = auth_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create presentation
    doc_content = (
        "# AI Slide Synthesis Engine\n\n"
        "## Problem Formulation\n"
        "- Slide generation without span grounding causes hallucination.\n"
        "- Manual formatting in presentation tools is repetitive.\n\n"
        "## Empirical Performance\n"
        "- Grounding verification accuracy is 96.8%.\n"
        "- Synthesis latency is 240 ms per deck.\n\n"
        "## Engineering Roadmap\n"
        "- Deploy OIDC Keycloak authentication across cluster.\n"
    )

    create_payload = {
        "title": "Atlas Hub Architecture Brief",
        "topic": "AI/ML developer tools",
        "raw_content": doc_content,
        "template_id": "modern-navy",
        "aspect_ratio": "16:9",
    }
    create_resp = client.post("/api/presentations", json=create_payload, headers=headers)
    assert create_resp.status_code == 201
    created = create_resp.json()
    pres_id = created["id"]
    assert created["title"] == "Atlas Hub Architecture Brief"
    assert len(created["slides"]) >= 4

    # 3. Read list
    list_resp = client.get("/api/presentations", headers=headers)
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert list_data["total"] >= 1
    assert any(p["id"] == pres_id for p in list_data["items"])

    # 4. Read detail
    detail_resp = client.get(f"/api/presentations/{pres_id}", headers=headers)
    assert detail_resp.status_code == 200
    assert detail_resp.json()["id"] == pres_id

    # 5. Run evaluation (attribution guard + 4-pillar scorecard)
    eval_resp = client.post(f"/api/presentations/{pres_id}/evaluate", headers=headers)
    assert eval_resp.status_code == 200
    eval_data = eval_resp.json()
    assert eval_data["overall_score"] > 50.0
    assert eval_data["grounding_score"] >= 60.0

    # Read latest evaluation
    get_eval_resp = client.get(f"/api/presentations/{pres_id}/evaluation", headers=headers)
    assert get_eval_resp.status_code == 200
    assert get_eval_resp.json()["overall_score"] == eval_data["overall_score"]

    # 6. Export native PPTX binary
    export_resp = client.get(f"/api/presentations/{pres_id}/export/pptx", headers=headers)
    assert export_resp.status_code == 200
    assert len(export_resp.content) > 1000
    assert export_resp.content.startswith(b"PK\x03\x04")

    # 7. Generate narration plan
    narration_resp = client.post(
        f"/api/presentations/{pres_id}/narration",
        json={"voice_id": "neutral-presenter", "target_wpm": 140},
        headers=headers,
    )
    assert narration_resp.status_code == 200
    narration_data = narration_resp.json()
    assert narration_data["total_duration_seconds"] > 0
    assert len(narration_data["cues"]) >= 4

    # Export WebVTT subtitles
    vtt_resp = client.get(f"/api/presentations/{pres_id}/narration/vtt", headers=headers)
    assert vtt_resp.status_code == 200
    assert "WEBVTT" in vtt_resp.text

    # 8. Update presentation metadata
    update_resp = client.put(
        f"/api/presentations/{pres_id}",
        json={"title": "Updated Atlas Hub Brief", "template_id": "emerald-clean"},
        headers=headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["title"] == "Updated Atlas Hub Brief"

    # 9. Delete presentation
    delete_resp = client.delete(f"/api/presentations/{pres_id}", headers=headers)
    assert delete_resp.status_code == 204

    # Verify not found after deletion
    get_del_resp = client.get(f"/api/presentations/{pres_id}", headers=headers)
    assert get_del_resp.status_code == 404


def test_boundary_and_malformed_inputs(client, analyst_token):
    """Verify validation boundaries and malformed input handling."""
    headers = {"Authorization": f"Bearer {analyst_token}"}

    # Too short raw_content (< 10 chars)
    short_resp = client.post(
        "/api/presentations",
        json={"title": "Too Short", "raw_content": "Short"},
        headers=headers,
    )
    assert short_resp.status_code == 422

    # Empty title
    empty_title_resp = client.post(
        "/api/presentations",
        json={"title": "", "raw_content": "Valid length content for test."},
        headers=headers,
    )
    assert empty_title_resp.status_code == 422

    # Query non-existent ID
    not_found_resp = client.get("/api/presentations/non-existent-uuid", headers=headers)
    assert not_found_resp.status_code == 404

    # Templates query is accessible
    tpl_resp = client.get("/api/templates", headers=headers)
    assert tpl_resp.status_code == 200
    assert len(tpl_resp.json()) >= 3
