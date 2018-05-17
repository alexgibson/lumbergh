from django.core.management import call_command
from django.test.utils import override_settings
from django.utils.six import StringIO

from mock import patch

from careers.base.tests import TestCase
from careers.careers.models import Position
from careers.careers.tests import PositionFactory


REQUESTS = 'careers.careers.management.commands.sync_greenhouse.requests'


@override_settings(GREENHOUSE_BOARD_TOKEN='mozilla')
class SyncGreenhouseTests(TestCase):
    def test_job_fetch(self):
        jobs_response = {
            'jobs': [
                {
                    'id': 'xxx',
                    'internal_job_id': 144381,
                    'title': 'Web Fox',
                    'updated_at': '2016-07-25T14:45:57-04:00',
                    'absolute_url': 'http://example.com/foo',
                    'content': '&lt;h2&gt;foo&lt;/h2&gt; bar',
                    "metadata": [
                        {
                            "id": 69450,
                            "name": "Employment Type",
                            "value": "Full-time",
                            "value_type": "single_select"
                        }
                    ],
                    'departments': [
                        {
                            'id': 13585,
                            'name': 'Engineering'
                        }
                    ],
                    'offices': [
                        {
                            'id': 1,
                            'name': 'Greece',
                        },
                        {
                            'id': 2,
                            'name': 'Remote',
                        },
                        {
                            'id': 3,
                            'name': 'Portland',
                        },

                    ]
                },
            ]
        }
        with patch(REQUESTS) as requests:
            requests.get().json.return_value = jobs_response
            call_command('sync_greenhouse', stdout=StringIO())
        position = Position.objects.get()
        self.assertEqual(position.job_id, 'xxx')
        self.assertEqual(position.title, 'Web Fox')
        self.assertEqual(position.location_list, ['Greece', 'Portland', 'Remote'])
        self.assertEqual(position.department, 'Engineering')
        self.assertEqual(position.apply_url, 'http://example.com/foo')
        self.assertEqual(position.source, 'gh')
        self.assertEqual(position.position_type, 'Full-time')
        self.assertEqual(position.description, '<h4>foo</h4> bar')

    def test_job_removal(self):
        PositionFactory.create(job_id='xxx')
        PositionFactory.create(job_id='yyy')
        jobs_response = {
            'jobs': [
                {
                    'id': 'xxx',
                    'title': 'Web Fox',
                    'absolute_url': 'http://example.com/foo'
                },
            ]
        }
        with patch(REQUESTS) as requests:
            requests.get().json.return_value = jobs_response
            call_command('sync_greenhouse', stdout=StringIO())
        self.assertEqual(Position.objects.all().count(), 1)
        self.assertEqual(Position.objects.all()[0].job_id, 'xxx')

    def test_position_description_none(self):
        """
        Store empty string is Greenhouse returns None for position or description.
        """
        jobs_response = {
            'jobs': [
                {
                    'id': 'xxx',
                    'title': 'Web Fox',
                    'absolute_url': 'http://example.com/foo'
                },
            ]
        }
        with patch(REQUESTS) as requests:
            requests.get().json.return_value = jobs_response
            call_command('sync_greenhouse', stdout=StringIO())
        self.assertEqual(Position.objects.all().count(), 1)
        self.assertEqual(Position.objects.all()[0].position_type, '')
        self.assertEqual(Position.objects.all()[0].description, '')
