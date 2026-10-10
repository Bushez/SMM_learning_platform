from uuid import UUID

from app.domain.photo_lab import PhotoAdjustments, PhotoPreset


class PhotoLabService:
    def list_master_presets(self) -> tuple[PhotoPreset, ...]:
        return (
            PhotoPreset(
                UUID("19d31588-2302-4773-a426-a06558eb162a"),
                "Чистый пейзаж",
                "Анна Светлова",
                "Естественный объём и прохладные света.",
                PhotoAdjustments(
                    exposure=0.25,
                    temperature=-8,
                    contrast=12,
                    highlights=-24,
                    shadows=18,
                    saturation=8,
                    aperture=8,
                    shutter_speed=1 / 125,
                    iso=100,
                ),
            ),
            PhotoPreset(
                UUID("ca814d81-3127-4df4-8bbb-c9e9734fa40f"),
                "Тёплый закат",
                "Михаил Рощин",
                "Тёплая плёнка, мягкие света.",
                PhotoAdjustments(
                    exposure=-3.5,
                    temperature=28,
                    tint=6,
                    contrast=-4,
                    highlights=-34,
                    shadows=12,
                    saturation=16,
                    aperture=4,
                    shutter_speed=1 / 80,
                    iso=200,
                ),
            ),
            PhotoPreset(
                UUID("979584ef-4d9c-4d25-952e-58be8dd66e33"),
                "Драматичный синий",
                "Ирина Волкова",
                "Холодная атмосфера и глубокий контраст.",
                PhotoAdjustments(
                    exposure=1.1,
                    temperature=-24,
                    tint=4,
                    contrast=28,
                    highlights=-18,
                    shadows=-12,
                    saturation=-6,
                    aperture=11,
                    shutter_speed=1 / 160,
                    iso=100,
                ),
            ),
        )
