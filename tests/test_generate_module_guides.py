from scripts.generate_module_guides import render_module_guide


def test_render_module_guide_contains_crm_orchestration_role() -> None:
    module = {
        "id": "forprint_crm",
        "title": "ForPrint CRM",
        "type": "business_orchestration_ui",
        "status": "planned",
        "role": "Бізнес-диригент, людський інтерфейс, прикладний оркестратор.",
        "owns": ["crm_dashboard_view"],
        "consumes": ["client"],
        "provides": ["business_command"],
        "must_not_own": ["canonical_client_registry"],
    }
    content = render_module_guide(module, flows=[], contracts=[])
    assert "Бізнес-диригент" in content
    assert "canonical_client_registry" in content
    assert "forprint_crm" in content
