#!/usr/bin/env python3

from marshmallow import Schema, fields
import json
from six.moves import configparser
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

        if attr in ['messageQuery', 'chartQuery'] and result is None:
            return ""

        elif attr in ['chartOptions', 'constraints'] and result is None:
            return None

        return json.dumps(result, sort_keys=True)


class AgentConfigString(fields.Field):
    """
    Custom field used to serialize/deserialize nested INI-like strings within the content pack.
    """

    def _deserialize(self, value, attr, data):
        config = configparser.ConfigParser()
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

        config = configparser.ConfigParser()
        config.__dict__['_sections'] = config_dict
        output = io.StringIO()
        config.write(output)
        return output.getvalue()


class FilterSchema(BaseContentSchema):
    internalName = fields.Str(attribute='internal_name', required=False)
    displayName = fields.Str(attribute='display_name', required=False)
    operator = fields.Str(required=False)
    value = fields.Str(allow_none=True, required=False)
    fieldType = fields.Str(attribute='field_type', required=False)
    isExtracted = fields.Bool(attribute='is_extracted', required=False)
    hidden = fields.Bool(required=False)


class ConstraintSchema(BaseContentSchema):
    searchTerms = fields.Str(attribute='search_terms', required=False)
    filters = fields.Nested(FilterSchema, many=True, required=False)


class ExtractedFieldSchema(BaseContentSchema):
    displayName = fields.Str(attribute='display_name', required=False)
    preContext = fields.Str(attribute='pre_context', required=False)
    postContext = fields.Str(attribute='post_context', required=False)
    regexValue = fields.Str(attribute='regex_value', required=False)
    internalName = fields.Str(attribute='internal_name', required=False)
    info = fields.Str(allow_none=True, required=False)
    constraints = JsonString(ConstraintSchema, allow_none=True, required=False)


class GroupByFieldSchema(BaseContentSchema):
    internalName = fields.Str(attribute='internal_name', required=False)
    numericGroupByType = fields.Str(attribute='numeric_group_by_type', required=False)
    displayName = fields.Str(attribute='display_name', required=False)
    numericGroupByValue = fields.Str(attribute='numeric_group_by_value', allow_none=True, required=False)
    displayNamespace = fields.Str(attribute='display_namespace', allow_none=True, required=False)


class PiqlFunctionSchema(BaseContentSchema):
    numericOnly = fields.Bool(attribute='numeric_only', required=False)
    requiresField = fields.Bool(attribute='requires_field', required=False)
    value = fields.Str(required=False)
    label = fields.Str(required=False)


class PiqlFunctionGroupsSchema(BaseContentSchema):
    field = fields.Nested(ExtractedFieldSchema, allow_none=True, required=True)
    functions = fields.Nested(PiqlFunctionSchema, many=True, required=True)


class QueryStringSchema(BaseContentSchema):
    groupByFields = fields.Nested(GroupByFieldSchema, attribute='group_by_fields', many=True, required=False)
    piqlFunction = fields.Nested(PiqlFunctionSchema, attribute='piql_function', required=False)
    endTimeMillis = fields.Int(attribute='end_time_millis', required=False)
    summarySortOrder = fields.Str(attribute='summary_sort_order', required=False)
    compareQueryOrderBy = fields.Str(attribute='compare_query_order_by', required=False)
    piqlFunctionField = fields.Str(attribute='piql_function_field', allow_none=True, required=False)
    shouldGroupByTime = fields.Bool(attribute='should_group_by_time', required=False)
    fieldConstraints = fields.Nested(FilterSchema, attribute='field_constraints', many=True, required=True)
    constraintToggle = fields.Str(attribute='constraint_toggle', required=False)
    eventSortOrder = fields.Str(attribute='event_sort_order', required=False)
    dateFilterPreset = fields.Str(attribute='date_filter_preset', required=False)
    compareQueryOptions = fields.Str(attribute='compare_query_options', allow_none=True, required=False)
    supplementalConstraints = fields.Nested(FilterSchema, attribute='supplemental_constraints', many=True, required=True)
    compareQuerySortOrder = fields.Str(attribute='compare_query_sort_order', required=False)
    messageViewType = fields.Str(attribute='message_view_type', required=False)
    query = fields.Str(required=False)
    startTimeMillis = fields.Int(attribute='start_time_millis', required=True)
    piqlFunctionGroups = fields.Nested(PiqlFunctionGroupsSchema, attribute='piql_function_groups', many=True,
                                       required=False)


class AlertSchema(BaseContentSchema):
    name = fields.Str(required=True)
    info = fields.Str(allow_none=True)
    alertType = fields.Str(attribute='alert_type', required=True)
    chartQuery = JsonString(QueryStringSchema, attribute='chart_query', allow_none=True, required=True)
    messageQuery = JsonString(QueryStringSchema, attribute='message_query', allow_none=True, required=False)
    recommendation = fields.Str(required=False)
    hitCount = fields.Float(attribute='hit_count', required=True)
    hitOperator = fields.Str(attribute='hit_operator', required=True)
    searchPeriod = fields.Int(attribute='search_period', required=True)
    searchInterval = fields.Int(attribute='search_interval', required=True)


class ChartOptionsSchema(BaseContentSchema):
    logaxis = fields.Bool(required=False)
    legend = fields.Bool(required=False)
    trendline = fields.Bool(required=False)
    spline = fields.Bool(required=False)


class ListDataOptionsSchema(BaseContentSchema):
    chartTypeName = fields.Str(attribute='chart_type_name', allow_none=True, required=False)
    chartOptions = JsonString(ChartOptionsSchema, attribute='chart_options', required=True)


class ListDataSchema(BaseContentSchema):
    name = fields.Str(required=True)
    chartQuery = JsonString(QueryStringSchema, attribute='chart_query', allow_none=True, required=True)
    messageQuery = JsonString(QueryStringSchema, attribute='message_query', allow_none=True, required=True)
    info = fields.Str(allow_none=True, required=True)
    options = JsonString(ListDataOptionsSchema, required=False)


class WidgetSchema(BaseContentSchema):
    name = fields.Str(required=True)
    info = fields.Str(allow_none=True, required=True)
    chartType = fields.Str(attribute='chart_type', allow_none=True, required=False)
    chartOptions = JsonString(ChartOptionsSchema, attribute='chart_options', allow_none=True, required=False)
    chartQuery = JsonString(QueryStringSchema, attribute='chart_query', allow_none=True, required=False)
    messageQuery = JsonString(QueryStringSchema, attribute='message_query', allow_none=True, required=False)
    listType = fields.Str(attribute='list_type', allow_none=False, required=False)
    listData = fields.Nested(ListDataSchema, attribute='list_data', many=True, required=False)
    columns = fields.Nested(GroupByFieldSchema, many=True, required=False)
    gridWidth = fields.Str(attribute='grid_width', required=False)
    widgetType = fields.Str(attribute='widget_type', required=True)


class RowSchema(BaseContentSchema):
    widgets = fields.Nested(WidgetSchema, many=True, required=True)


class ViewSchema(BaseContentSchema):
    name = fields.Str(required=True)
    constraints = fields.Nested(FilterSchema, many=True, required=True)  # called constraints, but actually a filter object
    rows = fields.Nested(RowSchema, many=True, required=True)


class DashboardSectionsSchema(BaseContentSchema):
    views = fields.Nested(ViewSchema, many=True, required=True)
    header = fields.Str(required=True)


class AgentClassesSchema(BaseContentSchema):
    name = fields.Str(required=True)
    info = fields.Str(allow_none=True, required=True)
    agentConfig = AgentConfigString(attribute='agent_config', required=True)


class AliasSchema(BaseContentSchema):
    key = fields.Str(required=True)
    value = fields.Str(required=True)


class AliasFieldsSchema(BaseContentSchema):
    name = fields.Str(required=True)
    searchField = fields.Str(attribute='search_field', required=True)
    aliases = fields.Nested(AliasSchema, many=True, required=True)


class AliasRulesSchema(BaseContentSchema):
    name = fields.Str(required=True)
    filter = fields.Str(required=True)
    keyField = fields.Str(attribute='key_field', required=True)
    valueField = fields.Str(attribute='value_field', required=True)
    aliasFieldName = fields.Str(attribute='alias_field_name', required=True)
    associatedFields = fields.List(fields.Str(), attribute='associated_fields', required=True)


class QueryOptionsSchema(BaseContentSchema):
    chartTypeName = fields.Str(attribute='chart_type_name', allow_none=True, required=True)
    chartOptions = JsonString(ChartOptionsSchema, attribute='chart_options', allow_none=True, required=True)


class QuerySchema(BaseContentSchema):
    name = fields.Str(required=True)
    chartQuery = JsonString(QueryStringSchema, attribute='chart_query', required=True)
    messageQuery = JsonString(QueryStringSchema, attribute='message_query', default="", allow_none=True, required=True)
    info = fields.Str(allow_none=True, required=False)
    options = JsonString(QueryOptionsSchema, allow_none=True, required=False)


class PackSchema(BaseContentSchema):
    name = fields.Str(required=True)
    namespace = fields.Str(required=True)
    contentPackId = fields.Str(attribute='content_pack_id', required=False)
    framework = fields.Str(required=True)
    version = fields.Str(required=True)
    author = fields.Str(required=True)
    url = fields.Str(required=True)  # should be validated
    contentVersion = fields.Str(attribute='content_version', required=True)
    info = fields.Str(allow_none=True, required=True)
    instructions = fields.Str(required=False)
    upgradeInstructions = fields.Str(required=False)
    icon = fields.Str(required=True)
    extractedFields = fields.Nested(ExtractedFieldSchema, attribute='extracted_fields', many=True, required=True)
    queries = fields.Nested(QuerySchema, many=True, required=True)
    alerts = fields.Nested(AlertSchema, many=True, required=True)
    dashboardSections = fields.Nested(DashboardSectionsSchema, attribute='dashboard_sections', many=True, required=True)
    agentClasses = fields.Nested(AgentClassesSchema, attribute='agent_classes', many=True, required=False)
    aliasFields = fields.Nested(AliasFieldsSchema, attribute='alias_fields', many=True, required=False)
    aliasRules = fields.Nested(AliasRulesSchema, attribute='alias_rules', many=True, required=False)
