#!/usr/bin/env python

from pyloginsight.content import PackSchema, QueryStringSchema, ConstraintSchema, ChartOptionsSchema, QueryOptionsSchema
from glob import glob
import json
import os
import re


def pytest_generate_tests(metafunc):

    if 'pack' in metafunc.fixturenames:

        packs = {}
        input_list = metafunc.config.getoption('--packs')

        # Support expanding home directory.
        for input_item in input_list:
            if '~' in input_item:
                expanded_input_item = os.path.expanduser(input_item)
            else:
                expanded_input_item = input_item

            # Support for globs.
            input_globs = glob(expanded_input_item)
            for file in input_globs:
                print(file)
                with open(file, 'r') as f:
                    try:
                        packs[file] = json.load(f)
                    except ValueError:
                        pass

        metafunc.parametrize('pack', packs.values(), ids=list(packs.keys()))


def test_pack(pack):
    first_pass_deserialized_pack = PackSchema().load(pack)
    assert first_pass_deserialized_pack.errors == {}

    first_pass_serialized_pack = PackSchema().dump(first_pass_deserialized_pack.data)
    assert first_pass_serialized_pack.errors == {}

    second_pass_deserialized_pack = PackSchema().load(first_pass_serialized_pack.data)
    assert second_pass_deserialized_pack.errors == {}

    second_pass_serialized_pack = PackSchema().dump(second_pass_deserialized_pack.data)
    assert second_pass_serialized_pack.errors == {}

    normalized_first_pass_json_string = json.dumps(first_pass_serialized_pack.data, indent=1, sort_keys=True)
    normalized_second_pass_json_string = json.dumps(second_pass_serialized_pack.data, indent=1, sort_keys=True)
    assert normalized_first_pass_json_string == normalized_second_pass_json_string

    # The following attempts to compare the original content pack value with the serialized values, but
    # certain keys with strings containing nested values are skipped because of varying uses of whitespace and quotes.
    stripped_pack_string = json.dumps(pack, indent=1, sort_keys=True)
    stripped_first_pass_string = normalized_first_pass_json_string
    stripped_second_pass_string = normalized_second_pass_json_string

    for bad_field in ['chartQuery', 'messageQuery', 'options', 'chartOptions', 'constraints', 'agentConfig']:
        pattern = re.compile('.*{}.+\n'.format(bad_field))
        stripped_pack_string = re.sub(pattern=pattern, repl='', string=stripped_pack_string)
        stripped_first_pass_string = re.sub(pattern=pattern, repl='', string=stripped_first_pass_string)
        stripped_second_pass_string = re.sub(pattern=pattern, repl='', string=stripped_second_pass_string)

    assert stripped_pack_string == stripped_first_pass_string
    assert stripped_pack_string == stripped_second_pass_string


def test_query_strings(pack):
    for alert in pack.get('alerts', []):
        for key in ['chartQuery', 'messsageQuery']:
            try:
                query_string = json.loads(alert.get(key))
                first_pass_deserialize = QueryStringSchema().load(query_string)
            except TypeError:
                print('Key is {} and caused TypeError'.format(alert.get(key)))
                continue
            except ValueError:
                print('Key is {} and caused ValueError.'.format(alert.get(key)))
                continue

            assert first_pass_deserialize.errors == {}

    for query in pack.get('queries', []):
        for key in ['chartQuery', 'messsageQuery']:
            try:
                query_string = json.loads(query.get(key))
                first_pass_deserialize = QueryStringSchema().load(query_string)
            except TypeError:
                print('Key is {} and caused TypeError'.format(query.get(key)))
                continue
            except ValueError:
                print('Key is {} and caused ValueError.'.format(query.get(key)))
                continue

            assert first_pass_deserialize.errors == {}


def test_constraints(pack):
    for extracted_field in pack.get('extractedFields', []):
        try:
            constraint_string = json.loads(extracted_field.get('constraints'))
            first_pass_deserialize = ConstraintSchema().load(constraint_string)
        except TypeError:
            print('Key is {} and caused TypeError'.format(extracted_field.get('constraints')))
            continue
        except ValueError:
            print('Key is {} and caused ValueError.'.format(extracted_field.get('constraints')))
            continue

        assert first_pass_deserialize.errors == {}


def test_widget_chart_options(pack):

    for dashboard_section in pack.get('dashboardSection', []):
        for view in dashboard_section.get('views', []):
            for row in view.get('row', []):
                for widget in row.get('widgets', []):
                    try:
                        chart_option_string = json.loads(widget.get('chartOptions'))
                        first_pass_deserialize = ChartOptionsSchema().load(chart_option_string)
                    except TypeError:
                        print('Key is {} and caused TypeError'.format(widget.get('chartOptions')))
                        continue
                    except ValueError:
                        print('Key is {} and caused ValueError.'.format(widget.get('chartOptions')))
                        continue

                    assert first_pass_deserialize.errors == {}


def test_list_data_options(pack):

    for dashboard_section in pack.get('dashboardSection', []):
        for view in dashboard_section.get('views', []):
            for row in view.get('row', []):
                for widget in row.get('widgets', []):
                    for list_data in widget.get('listData', []):
                        try:
                            list_data_option_string = json.loads(list_data.get('options'))
                            first_pass_deserialize = QueryOptionsSchema().load(list_data_option_string)
                        except TypeError:
                            print('Key is {} and caused TypeError'.format(list_data.get('options')))
                            continue
                        except ValueError:
                            print('Key is {} and caused ValueError.'.format(list_data.get('options')))
                            continue

                        assert first_pass_deserialize.errors == {}
