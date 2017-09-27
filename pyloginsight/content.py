#!/usr/bin/env python3

from marshmallow import Schema, fields
import json
from configparser import ConfigParser
import io


class BaseContentSchema(Schema):
    pass


class JsonString(fields.Nested):
    """
    Custom field used to serialize/deserialize nested JSON strings within the content pack.
    """

    def __init__(self, *args, **kwargs):
        super(JsonString, self).__init__(*args, **kwargs)
        self._cls = self.nested

    def _deserialize(self, value, attr, data):
        try:
            return super(JsonString, self)._deserialize(value=json.loads(value), attr=attr, data=data)
        except ValueError:
            return None

    def _serialize(self, nested_obj, attr, obj):
        result = super(JsonString, self)._serialize(nested_obj=nested_obj, attr=attr, obj=obj)
        return json.dumps(result, sort_keys=True)


class AgentConfigString(fields.Field):
    """
    Custom field used to serialize/deserialize nested INI-like strings within the content pack.
    """

    def _deserialize(self, value, attr, data):
        config = ConfigParser()
        config.read_string(value)
        config_dict = config.__dict__['_sections']

        for section_key, section_value in config_dict.items():
            for key, value in section_value.items():
                if key == 'tags':
                    config_dict[section_key]['tags'] = json.loads(value)

        return config_dict

    def _serialize(self, value, attr, obj):
        config_dict = super(AgentConfigString, self)._serialize(value=value, attr=attr, obj=obj)

        for section_key, section_value in config_dict.items():
            for key, value in section_value.items():
                if key == 'tags':
                    config_dict[section_key]['tags'] = json.dumps(value, sort_keys=True)

        config = ConfigParser()
        config.__dict__['_sections'] = config_dict
        output = io.StringIO()
        config.write(output)
        return output.getvalue()


class FilterSchema(BaseContentSchema):
    internalName = fields.Str(attribute='internal_name')
    displayName = fields.Str(attribute='display_name')
    operator = fields.Str()
    value = fields.Str(allow_none=True)
    fieldType = fields.Str(attribute='field_type')
    isExtracted = fields.Bool(attribute='is_extracted')
    hidden = fields.Bool()


class ConstraintSchema(BaseContentSchema):
    searchTerms = fields.Str(attribute='search_terms')
    filters = fields.Nested(FilterSchema, many=True)


class ExtractedFieldSchema(BaseContentSchema):
    displayName = fields.Str(attribute='display_name')
    preContext = fields.Str(attribute='pre_context')
    postContext = fields.Str(attribute='post_context')
    regexValue = fields.Str(attribute='regex_value')
    internalName = fields.Str(attribute='internal_name')
    info = fields.Str(required=False, allow_none=True)
    constraints = JsonString(ConstraintSchema, allow_none=True)


class GroupByFieldSchema(BaseContentSchema):
    internalName = fields.Str(attribute='internal_name')
    numericGroupByType = fields.Str(attribute='numeric_group_by_type')
    displayName = fields.Str(attribute='display_name')
    numericGroupByValue = fields.Str(attribute='numeric_group_by_value', allow_none=True)
    displayNamespace = fields.Str(attribute='display_namespace', allow_none=True)


class PiqlFunctionSchema(BaseContentSchema):
    numericOnly = fields.Bool(attribute='numeric_only')
    requiresField = fields.Bool(attribute='requires_field')
    value = fields.Str()
    label = fields.Str()


class PiqlFunctionGroupsSchema(BaseContentSchema):
    field = fields.Nested(ExtractedFieldSchema, allow_none=True)
    functions = fields.Nested(PiqlFunctionSchema, many=True)


class QueryStringSchema(BaseContentSchema):
    groupByFields = fields.Nested(GroupByFieldSchema, attribute='group_by_fields', many=True)
    piqlFunction = fields.Nested(PiqlFunctionSchema, attribute='piql_function')
    endTimeMillis = fields.Int(attribute='end_time_millis')
    summarySortOrder = fields.Str(attribute='summary_sort_order')
    compareQueryOrderBy = fields.Str(attribute='compare_query_order_by')
    piqlFunctionField = fields.Str(attribute='piql_function_field', allow_none=True)
    shouldGroupByTime = fields.Bool(attribute='should_group_by_time')
    fieldConstraints = fields.Nested(FilterSchema, attribute='field_constraints', many=True)
    constraintToggle = fields.Str(attribute='constraint_toggle')
    eventSortOrder = fields.Str(attribute='event_sort_order')
    dateFilterPreset = fields.Str(attribute='date_filter_preset')
    compareQueryOptions = fields.Str(attribute='compare_query_options', allow_none=True)
    supplementalConstraints = fields.Nested(FilterSchema, attribute='supplemental_constraints', many=True)
    compareQuerySortOrder = fields.Str(attribute='compare_query_sort_order')
    messageViewType = fields.Str(attribute='message_view_type')
    query = fields.Str()
    startTimeMillis = fields.Int(attribute='start_time_millis')
    piqlFunctionGroups = fields.Nested(PiqlFunctionGroupsSchema, attribute='piql_function_groups', many=True)


class AlertSchema(BaseContentSchema):
    name = fields.Str()
    info = fields.Str(allow_none=True)
    alertType = fields.Str(attribute='alert_type')
    chartQuery = JsonString(QueryStringSchema, attribute='chart_query', allow_none=True)
    messageQuery = JsonString(QueryStringSchema, attribute='message_query', allow_none=True)
    hitCount = fields.Float(attribute='hit_count')
    hitOperator = fields.Str(attribute='hit_operator')
    searchPeriod = fields.Int(attribute='search_period')
    searchInterval = fields.Int(attribute='search_interval')


class ChartOptionsSchema(BaseContentSchema):
    logaxis = fields.Bool()
    legend = fields.Bool()
    trendline = fields.Bool()
    spline = fields.Bool()


class ListDataOptionsSchema(BaseContentSchema):
    chartTypeName = fields.Str(attribute='chart_type_name', allow_none=True)
    chartOptions = JsonString(ChartOptionsSchema, attribute='chart_options')


class ListDataSchema(BaseContentSchema):
    name = fields.Str()
    chartQuery = JsonString(QueryStringSchema, attribute='chart_query', allow_none=True)
    messageQuery = JsonString(QueryStringSchema, attribute='message_query', allow_none=True)
    info = fields.Str(allow_none=True)
    options = JsonString(ListDataOptionsSchema)


class WidgetSchema(BaseContentSchema):
    name = fields.Str()
    info = fields.Str(allow_none=True)
    chartType = fields.Str(attribute='chart_type', allow_none=True)
    chartOptions = JsonString(ChartOptionsSchema, attribute='chart_options', allow_none=True)
    chartQuery = JsonString(QueryStringSchema, attribute='chart_query', allow_none=True)
    messageQuery = JsonString(QueryStringSchema, attribute='message_query', allow_none=True)
    listType = fields.Str(attribute='list_type', required=False, allow_none=True)
    listData = fields.Nested(ListDataSchema, attribute='list_data', required=False, many=True)
    columns = fields.Nested(GroupByFieldSchema, required=False, many=True)
    gridWidth = fields.Str(required=False, attribute='grid_width')
    widgetType = fields.Str(required=False, attribute='grid_width')


class RowSchema(BaseContentSchema):
    widgets = fields.Nested(WidgetSchema, many=True)


class ViewSchema(BaseContentSchema):
    name = fields.Str()
    constraints = fields.Nested(FilterSchema, many=True)  # called constraints, but actually a filter object
    rows = fields.Nested(RowSchema, many=True)


class DashboardSectionsSchema(BaseContentSchema):
    views = fields.Nested(ViewSchema, many=True)
    header = fields.Str()


class AgentClassesSchema(BaseContentSchema):
    name = fields.Str()
    info = fields.Str(allow_none=True)
    agentConfig = AgentConfigString(attribute='agent_config')


class AliasSchema(BaseContentSchema):
    key = fields.Str()
    value = fields.Str()


class AliasFieldsSchema(BaseContentSchema):
    name = fields.Str()
    searchField = fields.Str(attribute='search_field')
    aliases = fields.Nested(AliasSchema, many=True)


class AliasRulesSchema(BaseContentSchema):
    name = fields.Str()
    filter = fields.Str()
    keyField = fields.Str(attribute='key_field')
    valueField = fields.Str(attribute='value_field')
    aliasFieldName = fields.Str(attribute='alias_field_name')
    associatedFields = fields.List(fields.Str(), attribute='associated_fields')


class QueryOptionsSchema(BaseContentSchema):
    chartTypeName = fields.Str(attribute='chart_type_name', allow_none=True)
    chartOptions = JsonString(ChartOptionsSchema, attribute='chart_options', allow_none=True)


class QuerySchema(BaseContentSchema):
    name = fields.Str()
    chartQuery = JsonString(QueryStringSchema, attribute='chart_query')
    messageQuery = JsonString(QueryStringSchema, attribute='message_query', default="", allow_none=True)
    info = fields.Str(allow_none=True)
    options = JsonString(QueryOptionsSchema, allow_none=True)


class PackSchema(BaseContentSchema):
    name = fields.Str()
    namespace = fields.Str()
    contentPackId = fields.Str(attribute='content_pack_id')
    framework = fields.Str()
    version = fields.Str()
    author = fields.Str()
    url = fields.Str()  # should be validated
    contentVersion = fields.Str(attribute='content_version')
    info = fields.Str(allow_none=True)
    instructions = fields.Str()
    upgradeInstructions = fields.Str()
    icon = fields.Str()
    extractedFields = fields.Nested(ExtractedFieldSchema, attribute='extracted_fields', many=True)
    queries = fields.Nested(QuerySchema, many=True)
    alerts = fields.Nested(AlertSchema, many=True)
    dashboardSections = fields.Nested(DashboardSectionsSchema, attribute='dashboard_sections', many=True)
    agentClasses = fields.Nested(AgentClassesSchema, attribute='agent_classes', many=True)
    aliasFields = fields.Nested(AliasFieldsSchema, attribute='alias_fields', many=True)
    aliasRules = fields.Nested(AliasRulesSchema, attribute='alias_rules', many=True)
