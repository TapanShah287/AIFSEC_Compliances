# manager_entities/tests.py
from django.test import TestCase
from django.urls import reverse
from .models import ManagerEntity

class ManagerEntityViewsTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Create a test object once for all test methods
        cls.manager = ManagerEntity.objects.create(name="Test Manager Inc.")

    def test_manager_list_view(self):
        """Tests that the manager list page loads correctly."""
        response = self.client.get(reverse('manager_entities:manager_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.manager.name)
        self.assertTemplateUsed(response, 'manager_entities/manager_list.html')

    def test_manager_detail_view(self):
        """Tests that the manager detail page loads correctly."""
        response = self.client.get(reverse('manager_entities:manager_detail', args=[self.manager.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.manager.name)
        self.assertTemplateUsed(response, 'manager_entities/manager_detail.html')

    def test_manager_create_view(self):
        """Tests that a new manager can be created."""
        response = self.client.post(reverse('manager_entities:manager_create'), {
            'name': 'New Manager LLC',
            'pan': 'ABCDE1234F'
        })
        
        # Should redirect to the new detail page on success
        self.assertEqual(response.status_code, 302)
        
        # Verify the new manager exists in the database
        self.assertTrue(ManagerEntity.objects.filter(name="New Manager LLC").exists())

    def test_manager_update_view(self):
        """Tests that an existing manager can be updated."""
        response = self.client.post(reverse('manager_entities:manager_update', args=[self.manager.pk]), {
            'name': 'Updated Manager Name',
            'pan': 'FGHIJ5678K'
        })

        # Should redirect to the detail page on success
        self.assertEqual(response.status_code, 302)

        # Refresh the object from the database and check if the name was updated
        self.manager.refresh_from_db()
        self.assertEqual(self.manager.name, "Updated Manager Name")