from app.application.photo_lab import PhotoLabService


def test_master_presets_have_distinct_ids_and_camera_settings() -> None:
    presets = PhotoLabService().list_master_presets()

    assert len(presets) >= 3
    assert len({preset.id for preset in presets}) == len(presets)
    assert all(preset.author_name for preset in presets)
    assert all(preset.adjustments.iso >= 100 for preset in presets)
