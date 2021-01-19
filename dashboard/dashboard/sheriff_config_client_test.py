# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json

from dashboard import speed_releasing
from dashboard import sheriff_config_client
from dashboard.common import testing_common
from dashboard.models.subscription import Subscription
from dashboard.models.subscription import VISIBILITY
import mock

_SAMPLE_BOTS = ['ChromiumPerf/win', 'ChromiumPerf/linux']
_DOWNSTREAM_BOTS = ['ClankInternal/win', 'ClankInternal/linux']
_SAMPLE_TESTS = ['my_test_suite/my_test', 'my_test_suite/my_other_test']
_SAMPLE_LAYOUT = ('{ "my_test_suite/my_test": ["Foreground", '
                  '"Pretty Name 1"],"my_test_suite/my_other_test": '
                  ' ["Foreground", "Pretty Name 2"]}')

RECENT_REV = speed_releasing.CHROMIUM_MILESTONES[
    speed_releasing.CURRENT_MILESTONE][0] + 42


@mock.patch.object(sheriff_config_client.SheriffConfigClient, '_InitSession',
                   mock.MagicMock(return_value=None))
class SheriffConfigClientTest(testing_common.TestCase):

  class _Response(object):
    # pylint: disable=invalid-name

    def __init__(self, ok, text):
      self.ok = ok
      self.text = text

    def json(self):
      return json.loads(self.text)

    def status_code(self):
      return 200

  class _Session(object):

    def __init__(self, response):
      self._response = response

    def get(self, *_args, **_kargs):
      # pylint: disable=unused-argument
      return self._response

    def post(self, *_args, **_kargs):
      # pylint: disable=unused-argument
      return self._response

  def testMatch(self):
    clt = sheriff_config_client.SheriffConfigClient()
    response_text = """
    {
      "subscriptions": [
        {
          "config_set": "projects/catapult",
          "revision": "c9d4943dc832e448f9786e244f918fdabc1e5303",
          "subscription": {
            "name": "Public Team1",
            "rotation_url": "https://some/url",
            "notification_email": "public@mail.com",
            "monorail_project_id": "non-chromium",
            "bug_labels": [
              "Lable1",
              "Lable2"
            ],
            "bug_components": [
              "foo>bar"
            ],
            "visibility": "PUBLIC"
          }
        }
      ]
    }
    """
    clt._session = self._Session(self._Response(True, response_text))
    expected = [
        Subscription(
            revision='c9d4943dc832e448f9786e244f918fdabc1e5303',
            name='Public Team1',
            rotation_url='https://some/url',
            notification_email='public@mail.com',
            visibility=VISIBILITY.PUBLIC,
            bug_labels=['Lable1', 'Lable2'],
            bug_components=['foo>bar'],
            auto_triage_enable=False,
            auto_bisect_enable=False,
            monorail_project_id='non-chromium',
        ),
    ]
    self.assertEqual(clt.Match('Foo2/a/Bar2/b'), (expected, None))

  def testList(self):
    clt = sheriff_config_client.SheriffConfigClient()
    response_text = """
    {
      "subscriptions": [
        {
          "config_set": "projects/catapult",
          "revision": "c9d4943dc832e448f9786e244f918fdabc1e5303",
          "subscription": {
            "name": "Public Team1",
            "rotation_url": "https://some/url",
            "monorail_project_id": "non-chromium",
            "notification_email": "public@mail.com",
            "bug_labels": [
              "Lable1",
              "Lable2"
            ],
            "bug_components": [
              "foo>bar"
            ],
            "visibility": "PUBLIC"
          }
        }
      ]
    }
    """
    clt._session = self._Session(self._Response(True, response_text))
    expected = [
        Subscription(
            revision='c9d4943dc832e448f9786e244f918fdabc1e5303',
            name='Public Team1',
            rotation_url='https://some/url',
            notification_email='public@mail.com',
            visibility=VISIBILITY.PUBLIC,
            bug_labels=['Lable1', 'Lable2'],
            bug_components=['foo>bar'],
            auto_triage_enable=False,
            auto_bisect_enable=False,
            monorail_project_id='non-chromium',
        ),
    ]
    self.assertEqual(clt.List(), (expected, None))

  def testMatchFailed(self):
    clt = sheriff_config_client.SheriffConfigClient()
    clt._session = self._Session(self._Response(False, 'some error message'))
    res, err_msg = clt.Match('Foo2/a/Bar2/b')
    self.assertIsNone(res)
    self.assertIn('some error message', err_msg)

  def testMatchFailedCheck(self):
    clt = sheriff_config_client.SheriffConfigClient()
    clt._session = self._Session(self._Response(False, 'some error message'))
    with self.assertRaises(sheriff_config_client.InternalServerError):
      clt.Match('Foo2/a/Bar2/b', check=True)
