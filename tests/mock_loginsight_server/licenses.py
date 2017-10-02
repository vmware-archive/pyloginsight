# -*- coding: utf-8 -*-
import requests_mock
from collections import Counter
import json
import logging
from .utils import RandomDict, requiresauthentication, guid, uuid_url_matcher

mockserverlogger = logging.getLogger("LogInsightMockAdapter")


class MockedLicensesMixin(requests_mock.Adapter):

    def __init__(self, **kwargs):
        super(MockedLicensesMixin, self).__init__(**kwargs)

        self.licenses_known = RandomDict({'12345678-90ab-cdef-1234-567890abcdef': {'typeEnum': 'OSI', 'id': '12345678-90ab-cdef-1234-567890abcdef', 'error': '', 'status': 'Active', 'configuration': '1 Operating System Instance (OSI)', 'licenseKey': '4J2TK-XXXXX-XXXXX-XXXXX-XXXXX', 'infinite': True, 'count': 0, 'expiration': 0}})

        # License Keys
        self.register_uri('GET', '/api/v1/licenses', status_code=200, text=self.callback_list_license)
        self.register_uri('POST', '/api/v1/licenses', status_code=201, text=self.callback_add_license)
        self.register_uri('DELETE', uuid_url_matcher('licenses'), status_code=200, text=self.callback_remove_license)

    @requiresauthentication
    def callback_list_license(self, request, context, session_id, user_id):
        return json.dumps(self.get_license_summary_object())

    @requiresauthentication
    def callback_add_license(self, request, context, session_id, user_id):
        body = request.json()
        newitem = {'typeEnum': 'OSI', 'id': 'TBD', 'error': '', 'status': 'Active',
                   'configuration': '1 Operating System Instance (OSI)',
                   'licenseKey': body['key'], 'infinite': True, 'count': 0, 'expiration': 0}
        newitem['id'] = self.licenses_known.append(newitem)
        return json.dumps(newitem)

    @guid
    @requiresauthentication
    def callback_remove_license(self, request, context, session_id, user_id, guid):

        try:
            del self.licenses_known[guid]
            mockserverlogger.info("Deleted license {0}".format(guid))
        except KeyError:
            mockserverlogger.info("Attempted to delete nonexistant license {0}".format(guid))
            context.status_code = 404
        return

    def get_license_summary_object(self):
        counts = Counter(OSI=0, CPU=0)
        for key, license in self.licenses_known.items():
            if not license['error']:
                counts[license['typeEnum']] += license["count"]

        return {"hasOsi": counts['OSI'] > 0,
                "hasCpu": counts['CPU'] > 0,
                "maxOsis": counts['OSI'],
                "maxCpus": counts['CPU'],
                "limitedLicenseCapabilities": ["QUERY", "RBAC", "UPGRADE", "ACTIVE_DIRECTORY", "CONTENT_PACK"],
                "standardLicenseCapabilities": ["FORWARDING", "RBAC", "UPGRADE", "CUSTOM_SSL", "ACTIVE_DIRECTORY", "CONTENT_PACK", "VSPHERE_FULL_SUPPORT", "CLUSTER", "IMPORT_CONTENT_PACKS", "QUERY", "ARCHIVE", "THIRD_PARTY_CONTENT_PACKS"],
                "uninitializedLicenseCapabilities": ["RBAC", "ACTIVE_DIRECTORY", "CONTENT_PACK"],
                "licenseState": "ACTIVE" if (counts['OSI'] + counts['CPU'] > 0) else "INACTIVE",
                "licenses": self.licenses_known,
                "hasTap": False}

    def prep(self):
        pass
