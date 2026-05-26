from django.test import TestCase
from core.models import HealthPackage, CareerApplication

class Phase2ModelTest(TestCase):
    def test_health_package_creation(self):
        pkg = HealthPackage.objects.create(name="Heart Checkup", price=5000, inclusions="ECG\nEcho")
        self.assertEqual(pkg.slug, "heart-checkup")
        self.assertTrue(pkg.is_active)

    def test_career_application_creation(self):
        app = CareerApplication.objects.create(
            name="Jane Doe", email="jane@example.com", 
            phone="1234567890", position="Nurse"
        )
        self.assertEqual(str(app), "Jane Doe - Nurse")
